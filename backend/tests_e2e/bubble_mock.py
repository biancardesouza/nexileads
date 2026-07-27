"""Respostas fixas do Bubble (login) e da BrasilAPI (consulta de CNPJ) usadas
pelo servidor de testes E2E (ver server.py) — mesmo mecanismo de mock via
`respx` que já é usado nos testes de integração
(backend/tests/routers/test_auth_router.py), só que registrado num router
global de processo em vez de um `TestClient` por teste.

As constantes E2E_* abaixo precisam ficar em sincronia com os valores usados
em frontend/e2e/fluxo-lead.spec.js (JS não pode importar direto deste módulo
Python) — se mudar um lado, mude o outro.
"""

import json

import httpx
import respx

from app.bubble_client import BUBBLE_LOGIN_URL

E2E_EMAIL = "e2e@nexileads.test"
E2E_SENHA = "senha-e2e-123"
E2E_BUBBLE_USER_ID = "bubble-e2e-1"
E2E_NOME = "Usuária E2E"

# 14 dígitos quaisquer servem: o respx intercepta a resposta inteira da
# BrasilAPI, então o dígito verificador do CNPJ nunca é validado de verdade.
E2E_CNPJ = "12345678000199"
E2E_RAZAO_SOCIAL = "Empresa E2E Testes Ltda"

BRASILAPI_URL = f"https://brasilapi.com.br/api/cnpj/v1/{E2E_CNPJ}"


def _responder_login(request: httpx.Request) -> httpx.Response:
    corpo = json.loads(request.content)
    if corpo.get("email") == E2E_EMAIL and corpo.get("password") == E2E_SENHA:
        return httpx.Response(
            200,
            json={
                "status": "success",
                "response": {
                    "status": "success",
                    "id": E2E_BUBBLE_USER_ID,
                    "email": E2E_EMAIL,
                    "name": E2E_NOME,
                    "telephone": "11912345678",
                    "photo_url": "",
                },
            },
        )
    return httpx.Response(
        200,
        json={"statusCode": 400, "reason": "INVALID_LOGIN_CREDENTIALS", "message": "credenciais inválidas"},
    )


def registrar_mocks() -> None:
    """Registra as rotas mockadas no router global do respx — quem chama
    precisa já ter ativado esse router com `respx.mock.start()`."""
    respx.post(BUBBLE_LOGIN_URL).mock(side_effect=_responder_login)
    respx.get(BRASILAPI_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "razao_social": E2E_RAZAO_SOCIAL,
                "uf": "SP",
                "municipio": "São Paulo",
                "ddd_telefone_1": "1140001000",
                "email": "contato@empresae2e.test",
                "cnae_fiscal_descricao": "Desenvolvimento de software",
                "descricao_situacao_cadastral": "ATIVA",
            },
        )
    )
    # A aba "Novos leads" busca automaticamente ao carregar a página
    # (LeadsPage.jsx chama buscarNovosLeads(true) no mount) — sem mockar essa
    # rota, a chamada bateria de verdade em minhareceita.org e (por não
    # combinar com nenhuma rota mockada) o respx recusaria com
    # AllMockedAssertionError, virando um 500 sem relação com o que o teste
    # está verificando. "Nenhum lead novo" é uma resposta válida e suficiente
    # aqui, já que o fluxo testado não usa essa aba.
    respx.get("https://minhareceita.org/").mock(
        return_value=httpx.Response(200, json={"data": [], "cursor": None})
    )
