import httpx
import pytest
import respx

from app.cnpj_api import (
    CnpjInvalido,
    CnpjNaoEncontrado,
    ConsultaIndisponivel,
    buscar_por_criterio,
    consultar_cnpj,
    formatar_cnpj,
    somente_digitos,
)

CNPJ_DIGITOS = "11222333000181"
CNPJ_FORMATADO = "11.222.333/0001-81"
BRASILAPI_URL = f"https://brasilapi.com.br/api/cnpj/v1/{CNPJ_DIGITOS}"
OPENCNPJ_URL = f"https://api.opencnpj.org/{CNPJ_DIGITOS}"
MINHA_RECEITA_URL = "https://minhareceita.org/"


# ---------------------------------------------------------------------------
# somente_digitos / formatar_cnpj
# ---------------------------------------------------------------------------


def test_somente_digitos_remove_pontuacao():
    assert somente_digitos("11.222.333/0001-81") == CNPJ_DIGITOS


def test_somente_digitos_ja_sem_pontuacao():
    assert somente_digitos(CNPJ_DIGITOS) == CNPJ_DIGITOS


def test_somente_digitos_com_none_retorna_vazio():
    assert somente_digitos(None) == ""


def test_somente_digitos_com_vazio_retorna_vazio():
    assert somente_digitos("") == ""


def test_formatar_cnpj_com_14_digitos():
    assert formatar_cnpj(CNPJ_DIGITOS) == CNPJ_FORMATADO


def test_formatar_cnpj_com_tamanho_errado_retorna_sem_formatar():
    assert formatar_cnpj("123") == "123"
    assert formatar_cnpj("1" * 15) == "1" * 15


# ---------------------------------------------------------------------------
# consultar_cnpj — validação de entrada (sem rede)
# ---------------------------------------------------------------------------


def test_consultar_cnpj_com_menos_de_14_digitos_levanta_invalido():
    with pytest.raises(CnpjInvalido):
        consultar_cnpj("123456")


def test_consultar_cnpj_com_mais_de_14_digitos_levanta_invalido():
    with pytest.raises(CnpjInvalido):
        consultar_cnpj(CNPJ_DIGITOS + "99")


# ---------------------------------------------------------------------------
# consultar_cnpj — BrasilAPI feliz, sem tentar OpenCNPJ
# ---------------------------------------------------------------------------


@respx.mock
def test_consultar_cnpj_com_brasilapi_ok_nao_tenta_opencnpj():
    rota_brasilapi = respx.get(BRASILAPI_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "razao_social": "Empresa Teste LTDA",
                "nome_fantasia": "Empresa Teste",
                "uf": "SP",
                "municipio": "São Paulo",
                "ddd_telefone_1": "(11) 4000-0000",
                "email": "contato@empresateste.com.br",
                "cnae_fiscal_descricao": "Desenvolvimento de software",
                "descricao_situacao_cadastral": "ativa",
            },
        )
    )
    rota_opencnpj = respx.get(OPENCNPJ_URL).mock(return_value=httpx.Response(200, json={}))

    resultado = consultar_cnpj(CNPJ_FORMATADO)

    assert resultado == {
        "cnpj": CNPJ_FORMATADO,
        "razao_social": "Empresa Teste LTDA",
        "uf": "SP",
        "municipio": "São Paulo",
        "telefone": "(11) 4000-0000",
        "email": "contato@empresateste.com.br",
        "segmento": "Desenvolvimento de software",
        "situacao_cadastral": "ATIVA",
        "fonte": "brasilapi",
    }
    assert rota_brasilapi.called
    assert not rota_opencnpj.called


@respx.mock
def test_consultar_cnpj_usa_ddd_telefone_2_quando_nao_ha_ddd_telefone_1():
    respx.get(BRASILAPI_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "razao_social": "Empresa Teste LTDA",
                "uf": "SP",
                "municipio": "São Paulo",
                "ddd_telefone_2": "(11) 5000-0000",
            },
        )
    )

    resultado = consultar_cnpj(CNPJ_FORMATADO)

    assert resultado["telefone"] == "(11) 5000-0000"


# ---------------------------------------------------------------------------
# consultar_cnpj — fallback para OpenCNPJ
# ---------------------------------------------------------------------------


@respx.mock
def test_consultar_cnpj_com_brasilapi_404_cai_para_opencnpj():
    rota_brasilapi = respx.get(BRASILAPI_URL).mock(return_value=httpx.Response(404))
    rota_opencnpj = respx.get(OPENCNPJ_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "razao_social": "Empresa OpenCNPJ LTDA",
                "uf": "RJ",
                "municipio": "Rio de Janeiro",
                "telefones": [{"ddd": "21", "numero": "30000000"}],
                "email": "contato@opencnpj.com.br",
                "cnaes": [
                    {"is_principal": False, "descricao": "Secundário"},
                    {"is_principal": True, "descricao": "Consultoria em TI"},
                ],
                "situacao_cadastral": "ativa",
            },
        )
    )

    resultado = consultar_cnpj(CNPJ_FORMATADO)

    assert resultado == {
        "cnpj": CNPJ_FORMATADO,
        "razao_social": "Empresa OpenCNPJ LTDA",
        "uf": "RJ",
        "municipio": "Rio de Janeiro",
        "telefone": "(21) 30000000",
        "email": "contato@opencnpj.com.br",
        "segmento": "Consultoria em TI",
        "situacao_cadastral": "ATIVA",
        "fonte": "opencnpj",
    }
    assert rota_brasilapi.called
    assert rota_opencnpj.called


@respx.mock
def test_consultar_cnpj_com_brasilapi_checksum_invalido_nao_tenta_opencnpj():
    rota_brasilapi = respx.get(BRASILAPI_URL).mock(return_value=httpx.Response(400))
    rota_opencnpj = respx.get(OPENCNPJ_URL).mock(return_value=httpx.Response(200, json={}))

    with pytest.raises(CnpjInvalido):
        consultar_cnpj(CNPJ_FORMATADO)

    assert rota_brasilapi.called
    assert not rota_opencnpj.called


@respx.mock
def test_consultar_cnpj_com_erro_de_rede_na_brasilapi_cai_para_opencnpj():
    respx.get(BRASILAPI_URL).mock(side_effect=httpx.ConnectError("conexão recusada"))
    respx.get(OPENCNPJ_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "razao_social": "Empresa OpenCNPJ LTDA",
                "uf": "RJ",
                "municipio": "Rio de Janeiro",
                "telefones": [],
                "cnaes": [],
            },
        )
    )

    resultado = consultar_cnpj(CNPJ_FORMATADO)

    assert resultado["fonte"] == "opencnpj"
    assert resultado["razao_social"] == "Empresa OpenCNPJ LTDA"


@respx.mock
def test_consultar_cnpj_com_404_nas_duas_apis_levanta_nao_encontrado():
    respx.get(BRASILAPI_URL).mock(return_value=httpx.Response(404))
    respx.get(OPENCNPJ_URL).mock(return_value=httpx.Response(404))

    with pytest.raises(CnpjNaoEncontrado):
        consultar_cnpj(CNPJ_FORMATADO)


@respx.mock
def test_consultar_cnpj_com_as_duas_apis_indisponiveis_levanta_consulta_indisponivel():
    respx.get(BRASILAPI_URL).mock(side_effect=httpx.ConnectError("conexão recusada"))
    respx.get(OPENCNPJ_URL).mock(side_effect=httpx.ConnectError("conexão recusada"))

    with pytest.raises(ConsultaIndisponivel):
        consultar_cnpj(CNPJ_FORMATADO)


@respx.mock
def test_consultar_cnpj_telefone_do_opencnpj_com_item_que_nao_e_dict():
    respx.get(BRASILAPI_URL).mock(return_value=httpx.Response(404))
    respx.get(OPENCNPJ_URL).mock(
        return_value=httpx.Response(
            200,
            json={"razao_social": "Empresa Telefone String", "uf": "SP", "telefones": ["11 4000-0000"]},
        )
    )

    resultado = consultar_cnpj(CNPJ_FORMATADO)

    assert resultado["telefone"] == "11 4000-0000"


@respx.mock
def test_consultar_cnpj_telefone_do_opencnpj_sem_telefones_fica_vazio():
    respx.get(BRASILAPI_URL).mock(return_value=httpx.Response(404))
    respx.get(OPENCNPJ_URL).mock(
        return_value=httpx.Response(
            200,
            json={"razao_social": "Empresa Sem Telefone", "uf": "SP"},
        )
    )

    resultado = consultar_cnpj(CNPJ_FORMATADO)

    assert resultado["telefone"] == ""
    assert resultado["segmento"] == ""


# ---------------------------------------------------------------------------
# buscar_por_criterio
# ---------------------------------------------------------------------------


@respx.mock
def test_buscar_por_criterio_com_sucesso_retorna_lista_normalizada_e_cursor():
    respx.get(MINHA_RECEITA_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "cnpj": CNPJ_DIGITOS,
                        "razao_social": "Empresa Teste LTDA",
                        "uf": "SP",
                        "municipio": "São Paulo",
                        "ddd_telefone_1": "(11) 4000-0000",
                        "cnae_fiscal_descricao": "Desenvolvimento de software",
                        "descricao_situacao_cadastral": "ativa",
                    }
                ],
                "cursor": "abc",
            },
        )
    )

    itens, cursor = buscar_por_criterio(uf="SP", cnae="6201-5/01", cursor=None, limit=50)

    assert cursor == "abc"
    assert len(itens) == 1
    assert itens[0]["fonte"] == "minha-receita"
    assert itens[0]["cnpj"] == CNPJ_FORMATADO
    assert itens[0]["razao_social"] == "Empresa Teste LTDA"
    assert itens[0]["situacao_cadastral"] == "ATIVA"


@respx.mock
def test_buscar_por_criterio_envia_params_corretamente():
    rota = respx.get(MINHA_RECEITA_URL).mock(
        return_value=httpx.Response(200, json={"data": [], "cursor": None})
    )

    buscar_por_criterio(uf="SP", cnae="6201-5/01", cursor="pagina-2", limit=25)

    request_enviada = rota.calls.last.request
    params = request_enviada.url.params
    assert params["uf"] == "SP"
    assert params["cnae"] == "6201-5/01"
    assert params["cursor"] == "pagina-2"
    assert params["limit"] == "25"


@respx.mock
def test_buscar_por_criterio_sem_uf_cnae_cursor_nao_envia_esses_params():
    rota = respx.get(MINHA_RECEITA_URL).mock(
        return_value=httpx.Response(200, json={"data": [], "cursor": None})
    )

    buscar_por_criterio()

    params = rota.calls.last.request.url.params
    assert "uf" not in params
    assert "cnae" not in params
    assert "cursor" not in params
    assert params["limit"] == "100"


@respx.mock
def test_buscar_por_criterio_sem_chave_data_levanta_consulta_indisponivel():
    respx.get(MINHA_RECEITA_URL).mock(return_value=httpx.Response(200, json={"erro": "algo"}))

    with pytest.raises(ConsultaIndisponivel):
        buscar_por_criterio()


@respx.mock
def test_buscar_por_criterio_com_erro_de_rede_levanta_consulta_indisponivel():
    respx.get(MINHA_RECEITA_URL).mock(side_effect=httpx.ConnectError("conexão recusada"))

    with pytest.raises(ConsultaIndisponivel):
        buscar_por_criterio()


@respx.mock
def test_buscar_por_criterio_com_resposta_http_de_erro_levanta_consulta_indisponivel():
    respx.get(MINHA_RECEITA_URL).mock(return_value=httpx.Response(500))

    with pytest.raises(ConsultaIndisponivel):
        buscar_por_criterio()


@respx.mock
def test_buscar_por_criterio_ignora_itens_que_nao_sao_dict():
    respx.get(MINHA_RECEITA_URL).mock(
        return_value=httpx.Response(200, json={"data": ["nao é um dict"], "cursor": None})
    )

    itens, cursor = buscar_por_criterio()

    assert itens == []
    assert cursor is None
