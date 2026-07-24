from datetime import datetime, timedelta, timezone

import httpx
import respx

from app.models import CnpjConsulta, Lead, User

CNPJ_DIGITOS = "11222333000181"
CNPJ_FORMATADO = "11.222.333/0001-81"
BRASILAPI_URL = f"https://brasilapi.com.br/api/cnpj/v1/{CNPJ_DIGITOS}"
OPENCNPJ_URL = f"https://api.opencnpj.org/{CNPJ_DIGITOS}"

DADOS_BRASILAPI = {
    "razao_social": "Empresa Teste LTDA",
    "uf": "SP",
    "municipio": "São Paulo",
    "ddd_telefone_1": "(11) 4000-0000",
    "email": "contato@empresateste.com.br",
    "cnae_fiscal_descricao": "Desenvolvimento de software",
    "descricao_situacao_cadastral": "ativa",
}


def _lead_payload(**overrides):
    dados = {
        "razao_social": "Empresa Teste LTDA",
        "cnpj": CNPJ_FORMATADO,
        "uf": "SP",
        "municipio": "São Paulo",
        "telefone": "(11) 4000-0000",
        "email": "contato@empresateste.com.br",
        "segmento": "Desenvolvimento de software",
    }
    dados.update(overrides)
    return dados


def _outro_usuario(db_session, sufixo="2"):
    outro = User(
        username=f"outra{sufixo}@example.com",
        nome="Outra Pessoa",
        hashed_password="placeholder",
        bubble_user_id=f"bubble-outro-{sufixo}",
        email=f"outra{sufixo}@example.com",
    )
    db_session.add(outro)
    db_session.commit()
    db_session.refresh(outro)
    return outro


# ---------------------------------------------------------------------------
# GET /leads/consultar-cnpj/{cnpj}
# ---------------------------------------------------------------------------


def test_consultar_cnpj_formato_invalido_retorna_400_sem_chamar_rede(client, auth_headers):
    with respx.mock:
        resp = client.get("/leads/consultar-cnpj/123456", headers=auth_headers)

    assert resp.status_code == 400


@respx.mock
def test_consultar_cnpj_sem_cache_busca_na_api_e_cria_cache(client, auth_headers, db_session):
    respx.get(BRASILAPI_URL).mock(return_value=httpx.Response(200, json=DADOS_BRASILAPI))

    resp = client.get(f"/leads/consultar-cnpj/{CNPJ_FORMATADO}", headers=auth_headers)

    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["razao_social"] == "Empresa Teste LTDA"
    assert corpo["fonte"] == "brasilapi"

    cache = db_session.query(CnpjConsulta).filter(CnpjConsulta.cnpj == CNPJ_DIGITOS).first()
    assert cache is not None
    assert cache.razao_social == "Empresa Teste LTDA"


def test_consultar_cnpj_com_cache_valido_nao_chama_rede_e_marca_fonte_cache(
    client, auth_headers, db_session
):
    cache = CnpjConsulta(
        cnpj=CNPJ_DIGITOS,
        razao_social="Empresa Cacheada LTDA",
        uf="SP",
        municipio="São Paulo",
        telefone="(11) 4000-0000",
        email="cache@empresateste.com.br",
        segmento="Comércio",
        situacao_cadastral="ATIVA",
        fonte="brasilapi",
        consultado_em=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(cache)
    db_session.commit()

    with respx.mock:
        resp = client.get(f"/leads/consultar-cnpj/{CNPJ_FORMATADO}", headers=auth_headers)

    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["razao_social"] == "Empresa Cacheada LTDA"
    assert corpo["fonte"] == "brasilapi (cache)"


@respx.mock
def test_consultar_cnpj_com_cache_expirado_busca_de_novo_e_atualiza(
    client, auth_headers, db_session
):
    cache = CnpjConsulta(
        cnpj=CNPJ_DIGITOS,
        razao_social="Empresa Velha LTDA",
        uf="SP",
        municipio="São Paulo",
        telefone="(11) 4000-0000",
        email="velha@empresateste.com.br",
        segmento="Comércio",
        situacao_cadastral="ATIVA",
        fonte="brasilapi",
        consultado_em=datetime.now(timezone.utc) - timedelta(days=31),
    )
    db_session.add(cache)
    db_session.commit()

    rota = respx.get(BRASILAPI_URL).mock(return_value=httpx.Response(200, json=DADOS_BRASILAPI))

    resp = client.get(f"/leads/consultar-cnpj/{CNPJ_FORMATADO}", headers=auth_headers)

    assert resp.status_code == 200
    assert rota.called
    corpo = resp.json()
    assert corpo["razao_social"] == "Empresa Teste LTDA"

    db_session.expire_all()
    cache_atualizado = (
        db_session.query(CnpjConsulta).filter(CnpjConsulta.cnpj == CNPJ_DIGITOS).first()
    )
    assert cache_atualizado.razao_social == "Empresa Teste LTDA"


@respx.mock
def test_consultar_cnpj_nao_encontrado_nas_duas_apis_retorna_404(client, auth_headers):
    respx.get(BRASILAPI_URL).mock(return_value=httpx.Response(404))
    respx.get(OPENCNPJ_URL).mock(return_value=httpx.Response(404))

    resp = client.get(f"/leads/consultar-cnpj/{CNPJ_FORMATADO}", headers=auth_headers)

    assert resp.status_code == 404


@respx.mock
def test_consultar_cnpj_ambas_apis_indisponiveis_retorna_503(client, auth_headers):
    respx.get(BRASILAPI_URL).mock(side_effect=httpx.ConnectError("conexão recusada"))
    respx.get(OPENCNPJ_URL).mock(side_effect=httpx.ConnectError("conexão recusada"))

    resp = client.get(f"/leads/consultar-cnpj/{CNPJ_FORMATADO}", headers=auth_headers)

    assert resp.status_code == 503


@respx.mock
def test_consultar_cnpj_com_checksum_invalido_na_brasilapi_retorna_400(client, auth_headers):
    # A BrasilAPI valida o dígito verificador e responde 400 mesmo para um
    # CNPJ com 14 dígitos — cnpj_api.consultar_cnpj propaga isso como
    # CnpjInvalido, que o router também deve traduzir para 400.
    respx.get(BRASILAPI_URL).mock(return_value=httpx.Response(400))

    resp = client.get(f"/leads/consultar-cnpj/{CNPJ_FORMATADO}", headers=auth_headers)

    assert resp.status_code == 400


def test_consultar_cnpj_sem_autenticacao_retorna_401(client):
    resp = client.get(f"/leads/consultar-cnpj/{CNPJ_FORMATADO}")

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /leads
# ---------------------------------------------------------------------------


def test_listar_leads_vazio_para_usuario_novo(client, auth_headers):
    resp = client.get("/leads", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.json() == []


def test_listar_leads_retorna_so_os_leads_do_usuario_ordenados_do_mais_recente(
    client, auth_headers, usuario, db_session
):
    outro = _outro_usuario(db_session)

    lead_antigo = Lead(
        owner_id=usuario.id,
        razao_social="Lead Antigo",
        cnpj="11.111.111/0001-11",
        uf="SP",
        municipio="São Paulo",
        telefone="(11) 1111-1111",
        email="antigo@x.com",
        segmento="Comércio",
    )
    db_session.add(lead_antigo)
    db_session.commit()

    lead_recente = Lead(
        owner_id=usuario.id,
        razao_social="Lead Recente",
        cnpj="22.222.222/0001-22",
        uf="RJ",
        municipio="Rio de Janeiro",
        telefone="(21) 2222-2222",
        email="recente@x.com",
        segmento="Serviços",
    )
    db_session.add(lead_recente)
    db_session.commit()

    lead_de_outro = Lead(
        owner_id=outro.id,
        razao_social="Lead de Outro Usuário",
        cnpj="33.333.333/0001-33",
        uf="MG",
        municipio="Belo Horizonte",
        telefone="(31) 3333-3333",
        email="outro@x.com",
        segmento="Indústria",
    )
    db_session.add(lead_de_outro)
    db_session.commit()

    resp = client.get("/leads", headers=auth_headers)

    assert resp.status_code == 200
    corpo = resp.json()
    assert [item["razao_social"] for item in corpo] == ["Lead Recente", "Lead Antigo"]


def test_listar_leads_sem_autenticacao_retorna_401(client):
    resp = client.get("/leads")

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /leads
# ---------------------------------------------------------------------------


def test_adicionar_lead_com_sucesso_retorna_201(client, auth_headers):
    resp = client.post("/leads", json=_lead_payload(), headers=auth_headers)

    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["cnpj"] == CNPJ_FORMATADO
    assert corpo["status"] == "sem_contato"
    assert corpo["registros"] == []


def test_adicionar_lead_com_cnpj_invalido_retorna_400(client, auth_headers):
    resp = client.post("/leads", json=_lead_payload(cnpj="123"), headers=auth_headers)

    assert resp.status_code == 400


def test_adicionar_lead_duplicado_para_mesmo_usuario_retorna_409(client, auth_headers):
    client.post("/leads", json=_lead_payload(), headers=auth_headers)

    resp = client.post("/leads", json=_lead_payload(), headers=auth_headers)

    assert resp.status_code == 409


def test_adicionar_lead_mesmo_cnpj_de_outro_usuario_e_permitido(
    client, auth_headers, db_session
):
    outro = _outro_usuario(db_session)
    lead_de_outro = Lead(
        owner_id=outro.id,
        cnpj=CNPJ_FORMATADO,
        razao_social="Empresa Teste LTDA",
        uf="SP",
        municipio="São Paulo",
        telefone="(11) 4000-0000",
        email="contato@empresateste.com.br",
        segmento="Desenvolvimento de software",
    )
    db_session.add(lead_de_outro)
    db_session.commit()

    resp = client.post("/leads", json=_lead_payload(), headers=auth_headers)

    assert resp.status_code == 201


def test_adicionar_lead_sem_autenticacao_retorna_401(client):
    resp = client.post("/leads", json=_lead_payload())

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /leads/{id}
# ---------------------------------------------------------------------------


def test_excluir_lead_do_proprio_usuario_retorna_204(client, auth_headers):
    criado = client.post("/leads", json=_lead_payload(), headers=auth_headers).json()

    resp = client.delete(f"/leads/{criado['id']}", headers=auth_headers)

    assert resp.status_code == 204
    assert client.get("/leads", headers=auth_headers).json() == []


def test_excluir_lead_inexistente_retorna_404(client, auth_headers):
    resp = client.delete("/leads/999999", headers=auth_headers)

    assert resp.status_code == 404


def test_excluir_lead_de_outro_usuario_retorna_404_e_nao_exclui(
    client, auth_headers, db_session
):
    outro = _outro_usuario(db_session)
    lead_de_outro = Lead(
        owner_id=outro.id,
        cnpj=CNPJ_FORMATADO,
        razao_social="Empresa Teste LTDA",
        uf="SP",
        municipio="São Paulo",
        telefone="(11) 4000-0000",
        email="contato@empresateste.com.br",
        segmento="Desenvolvimento de software",
    )
    db_session.add(lead_de_outro)
    db_session.commit()
    db_session.refresh(lead_de_outro)

    resp = client.delete(f"/leads/{lead_de_outro.id}", headers=auth_headers)

    assert resp.status_code == 404
    db_session.expire_all()
    assert db_session.query(Lead).filter(Lead.id == lead_de_outro.id).first() is not None


def test_excluir_lead_sem_autenticacao_retorna_401(client):
    resp = client.delete("/leads/1")

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /leads/{id}/registros
# ---------------------------------------------------------------------------


def test_salvar_registro_atualiza_status_e_adiciona_na_lista(client, auth_headers):
    criado = client.post("/leads", json=_lead_payload(), headers=auth_headers).json()

    resp = client.post(
        f"/leads/{criado['id']}/registros",
        json={"status": "contatado", "nota": "Falei com o financeiro"},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["status"] == "contatado"
    assert len(corpo["registros"]) == 1
    assert corpo["registros"][0]["nota"] == "Falei com o financeiro"
    assert corpo["registros"][0]["status"] == "contatado"


def test_salvar_registro_com_nota_vazia_usa_texto_padrao(client, auth_headers):
    criado = client.post("/leads", json=_lead_payload(), headers=auth_headers).json()

    resp = client.post(
        f"/leads/{criado['id']}/registros",
        json={"status": "sem_interesse", "nota": ""},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["registros"][0]["nota"] == "(sem anotação)"


def test_salvar_registro_lead_inexistente_retorna_404(client, auth_headers):
    resp = client.post(
        "/leads/999999/registros",
        json={"status": "contatado", "nota": "x"},
        headers=auth_headers,
    )

    assert resp.status_code == 404


def test_salvar_registro_lead_de_outro_usuario_retorna_404(client, auth_headers, db_session):
    outro = _outro_usuario(db_session)
    lead_de_outro = Lead(
        owner_id=outro.id,
        cnpj=CNPJ_FORMATADO,
        razao_social="Empresa Teste LTDA",
        uf="SP",
        municipio="São Paulo",
        telefone="(11) 4000-0000",
        email="contato@empresateste.com.br",
        segmento="Desenvolvimento de software",
    )
    db_session.add(lead_de_outro)
    db_session.commit()
    db_session.refresh(lead_de_outro)

    resp = client.post(
        f"/leads/{lead_de_outro.id}/registros",
        json={"status": "contatado", "nota": "x"},
        headers=auth_headers,
    )

    assert resp.status_code == 404


def test_salvar_registro_sem_autenticacao_retorna_401(client):
    resp = client.post("/leads/1/registros", json={"status": "contatado", "nota": "x"})

    assert resp.status_code == 401
