"""Cliente para o workflow de login exposto pelo app da empresa no Bubble.

O Bubble é a fonte única de autenticação: este módulo chama o Backend
Workflow "login" que roda a ação nativa "Log the user in" contra a tabela
de usuários do Bubble.

Os três formatos de resposta abaixo foram confirmados testando o endpoint
de verdade (não são só suposição):

1. Sucesso — {"status": "success", "response": {"status": "success",
   "id": ..., "email": ..., "name": ..., "telephone": ..., "photo_url": ...}}
2. Senha/e-mail inválidos — o Bubble propaga um erro nativo da própria ação
   "Log the user in" ANTES de chegar no nosso passo de "Return data", com um
   formato diferente: {"statusCode": 400, "reason": "INVALID_LOGIN_CREDENTIALS",
   "message": "..."}
3. Segredo (api_secret) errado — o workflow termina antes de tentar o login
   (ação "Terminate this workflow"), devolvendo
   {"status": "success", "response": {"user_id": "non_authenticated_user_..."}}
   sem nenhum dos campos esperados. Isso só deveria acontecer se o segredo
   configurado aqui e no Bubble ficarem dessincronizados — tratamos como
   indisponibilidade, não como senha errada.
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BUBBLE_LOGIN_URL = os.environ.get("BUBBLE_LOGIN_URL")
BUBBLE_API_SECRET = os.environ.get("BUBBLE_API_SECRET")

TIMEOUT_SEGUNDOS = 10.0


class BubbleIndisponivel(Exception):
    """Erro de rede/timeout ou resposta inesperada do Bubble — não diz nada
    sobre a credencial em si, então não deve virar 401 pro usuário."""


def autenticar_no_bubble(email: str, senha: str) -> dict | None:
    """Retorna os dados do usuário (com pelo menos id/email/name) em caso de
    sucesso, ou None se a credencial for inválida. Levanta BubbleIndisponivel
    se o Bubble não puder ser alcançado ou responder de forma inesperada."""
    if not BUBBLE_LOGIN_URL or not BUBBLE_API_SECRET:
        raise BubbleIndisponivel("BUBBLE_LOGIN_URL/BUBBLE_API_SECRET não configurados")

    try:
        resposta = httpx.post(
            BUBBLE_LOGIN_URL,
            json={"email": email, "password": senha, "api_secret": BUBBLE_API_SECRET},
            timeout=TIMEOUT_SEGUNDOS,
        )
    except httpx.HTTPError as exc:
        raise BubbleIndisponivel(f"falha de rede ao chamar o Bubble: {exc}") from exc

    try:
        corpo = resposta.json()
    except ValueError as exc:
        raise BubbleIndisponivel(f"resposta do Bubble não é JSON válido (HTTP {resposta.status_code})") from exc

    if corpo.get("status") != "success":
        # Erro nativo de uma ação que falhou sem "Return data" próprio (ex: a
        # ação "Log the user in" com credenciais inválidas).
        if corpo.get("reason") == "INVALID_LOGIN_CREDENTIALS":
            return None
        raise BubbleIndisponivel(f"resposta inesperada do Bubble: {corpo!r}")

    dados = corpo.get("response") or {}
    if dados.get("status") == "success" and dados.get("email"):
        return dados

    # Chegou aqui com "status: success" no nível externo mas sem os campos
    # esperados — normalmente sinal de que o api_secret não bateu (o
    # workflow terminou antes do login) ou o workflow no Bubble foi alterado.
    raise BubbleIndisponivel(f"resposta inesperada do Bubble: {corpo!r}")
