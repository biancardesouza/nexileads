import httpx
import respx

from app.cnpj_api import formatar_cnpj
from app.models import Lead, LeadOculto

MINHA_RECEITA_URL = "https://minhareceita.org/"

CNPJ_ATIVO_1 = "11111111000101"
CNPJ_ATIVO_2 = "22222222000102"
CNPJ_INATIVO = "33333333000103"


def _empresa(cnpj_digitos: str, situacao: str = "ativa", **overrides):
    dados = {
        "cnpj": cnpj_digitos,
        "razao_social": f"Empresa {cnpj_digitos}",
        "uf": "SP",
        "municipio": "São Paulo",
        "ddd_telefone_1": "(11) 4000-0000",
        "email": "contato@empresa.com.br",
        "cnae_fiscal_descricao": "Comércio",
        "descricao_situacao_cadastral": situacao,
    }
    dados.update(overrides)
    return dados


# ---------------------------------------------------------------------------
# GET /leads/novos
# ---------------------------------------------------------------------------


@respx.mock
def test_listar_novos_leads_retorna_so_empresas_ativas(client, auth_headers):
    respx.get(MINHA_RECEITA_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    _empresa(CNPJ_ATIVO_1, "ativa"),
                    _empresa(CNPJ_ATIVO_2, "ativa"),
                    _empresa(CNPJ_INATIVO, "baixada"),
                ],
                "cursor": None,
            },
        )
    )

    resp = client.get("/leads/novos?uf=SP", headers=auth_headers)

    assert resp.status_code == 200
    corpo = resp.json()
    cnpjs = {item["cnpj"] for item in corpo}
    assert cnpjs == {formatar_cnpj(CNPJ_ATIVO_1), formatar_cnpj(CNPJ_ATIVO_2)}
    assert formatar_cnpj(CNPJ_INATIVO) not in cnpjs


@respx.mock
def test_listar_novos_leads_exclui_cnpjs_ja_salvos_e_ja_ocultados(
    client, auth_headers, usuario, db_session
):
    lead_salvo = Lead(
        owner_id=usuario.id,
        cnpj=formatar_cnpj(CNPJ_ATIVO_1),
        razao_social="Já Salva",
        uf="SP",
        municipio="São Paulo",
        telefone="(11) 4000-0000",
        email="salva@x.com",
        segmento="Comércio",
    )
    db_session.add(lead_salvo)
    db_session.add(LeadOculto(owner_id=usuario.id, cnpj=formatar_cnpj(CNPJ_ATIVO_2)))
    db_session.commit()

    respx.get(MINHA_RECEITA_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    _empresa(CNPJ_ATIVO_1, "ativa"),
                    _empresa(CNPJ_ATIVO_2, "ativa"),
                    _empresa(CNPJ_INATIVO, "baixada"),
                ],
                "cursor": None,
            },
        )
    )

    resp = client.get("/leads/novos?uf=SP", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.json() == []


@respx.mock
def test_listar_novos_leads_envia_uf_e_cnae_para_api_externa(client, auth_headers):
    rota = respx.get(MINHA_RECEITA_URL).mock(
        return_value=httpx.Response(200, json={"data": [], "cursor": None})
    )

    resp = client.get("/leads/novos?uf=RJ&cnae=6201-5%2F01", headers=auth_headers)

    assert resp.status_code == 200
    params = rota.calls.last.request.url.params
    assert params["uf"] == "RJ"
    assert params["cnae"] == "6201-5/01"


@respx.mock
def test_listar_novos_leads_com_erro_de_rede_retorna_503(client, auth_headers):
    respx.get(MINHA_RECEITA_URL).mock(side_effect=httpx.ConnectError("conexão recusada"))

    resp = client.get("/leads/novos?uf=SP", headers=auth_headers)

    assert resp.status_code == 503


@respx.mock
def test_listar_novos_leads_com_resposta_sem_campo_data_retorna_503(client, auth_headers):
    respx.get(MINHA_RECEITA_URL).mock(return_value=httpx.Response(200, json={"algo": "errado"}))

    resp = client.get("/leads/novos?uf=SP", headers=auth_headers)

    assert resp.status_code == 503


@respx.mock
def test_listar_novos_leads_paginacao_para_quando_cursor_vem_nulo(client, auth_headers):
    resposta_pagina_1 = httpx.Response(
        200,
        json={
            "data": [
                _empresa(CNPJ_ATIVO_1, "ativa"),
            ],
            "cursor": "pagina-2",
        },
    )
    resposta_pagina_2 = httpx.Response(
        200,
        json={
            "data": [
                _empresa(CNPJ_ATIVO_2, "ativa"),
            ],
            "cursor": None,
        },
    )
    rota = respx.get(MINHA_RECEITA_URL).mock(
        side_effect=[resposta_pagina_1, resposta_pagina_2]
    )

    resp = client.get("/leads/novos?uf=SP", headers=auth_headers)

    assert resp.status_code == 200
    corpo = resp.json()
    cnpjs = {item["cnpj"] for item in corpo}
    assert cnpjs == {formatar_cnpj(CNPJ_ATIVO_1), formatar_cnpj(CNPJ_ATIVO_2)}
    # Parou de paginar assim que o cursor veio nulo na 2ª página — não chegou
    # a fazer uma 3ª chamada.
    assert rota.call_count == 2


def test_listar_novos_leads_sem_autenticacao_retorna_401(client):
    resp = client.get("/leads/novos")

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /leads/novos/ocultar
# ---------------------------------------------------------------------------


def test_ocultar_lead_cnpj_invalido_retorna_400(client, auth_headers):
    resp = client.post("/leads/novos/ocultar", json={"cnpj": "123"}, headers=auth_headers)

    assert resp.status_code == 400


def test_ocultar_lead_novo_cria_registro_e_retorna_204(client, auth_headers, usuario, db_session):
    resp = client.post(
        "/leads/novos/ocultar", json={"cnpj": formatar_cnpj(CNPJ_ATIVO_1)}, headers=auth_headers
    )

    assert resp.status_code == 204
    db_session.expire_all()
    ocultos = (
        db_session.query(LeadOculto)
        .filter(LeadOculto.owner_id == usuario.id, LeadOculto.cnpj == formatar_cnpj(CNPJ_ATIVO_1))
        .all()
    )
    assert len(ocultos) == 1


def test_ocultar_lead_ja_oculto_nao_duplica(client, auth_headers, usuario, db_session):
    cnpj = formatar_cnpj(CNPJ_ATIVO_1)

    resp1 = client.post("/leads/novos/ocultar", json={"cnpj": cnpj}, headers=auth_headers)
    resp2 = client.post("/leads/novos/ocultar", json={"cnpj": cnpj}, headers=auth_headers)

    assert resp1.status_code == 204
    assert resp2.status_code == 204
    db_session.expire_all()
    ocultos = (
        db_session.query(LeadOculto)
        .filter(LeadOculto.owner_id == usuario.id, LeadOculto.cnpj == cnpj)
        .all()
    )
    assert len(ocultos) == 1


def test_ocultar_lead_sem_autenticacao_retorna_401(client):
    resp = client.post("/leads/novos/ocultar", json={"cnpj": formatar_cnpj(CNPJ_ATIVO_1)})

    assert resp.status_code == 401
