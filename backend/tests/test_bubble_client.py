import httpx
import pytest
import respx

from app.bubble_client import BUBBLE_LOGIN_URL, BubbleIndisponivel, autenticar_no_bubble


@respx.mock
def test_autenticar_no_bubble_com_sucesso_retorna_dados_do_usuario():
    respx.post(BUBBLE_LOGIN_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "success",
                "response": {
                    "status": "success",
                    "id": "user-1",
                    "email": "usuaria@example.com",
                    "name": "Usuária Teste",
                    "telephone": "11999999999",
                    "photo_url": "https://example.com/foto.png",
                },
            },
        )
    )

    resultado = autenticar_no_bubble("usuaria@example.com", "senha-correta")

    assert resultado == {
        "status": "success",
        "id": "user-1",
        "email": "usuaria@example.com",
        "name": "Usuária Teste",
        "telephone": "11999999999",
        "photo_url": "https://example.com/foto.png",
    }


@respx.mock
def test_autenticar_no_bubble_com_credenciais_invalidas_retorna_none():
    respx.post(BUBBLE_LOGIN_URL).mock(
        return_value=httpx.Response(
            400,
            json={
                "statusCode": 400,
                "reason": "INVALID_LOGIN_CREDENTIALS",
                "message": "credenciais inválidas",
            },
        )
    )

    resultado = autenticar_no_bubble("usuaria@example.com", "senha-errada")

    assert resultado is None


@respx.mock
def test_autenticar_no_bubble_com_api_secret_errado_levanta_indisponivel():
    respx.post(BUBBLE_LOGIN_URL).mock(
        return_value=httpx.Response(
            200,
            json={"status": "success", "response": {"user_id": "non_authenticated_user_xyz"}},
        )
    )

    with pytest.raises(BubbleIndisponivel):
        autenticar_no_bubble("usuaria@example.com", "senha-correta")


@respx.mock
def test_autenticar_no_bubble_com_erro_de_rede_levanta_indisponivel():
    respx.post(BUBBLE_LOGIN_URL).mock(side_effect=httpx.ConnectError("conexão recusada"))

    with pytest.raises(BubbleIndisponivel):
        autenticar_no_bubble("usuaria@example.com", "senha-correta")


@respx.mock
def test_autenticar_no_bubble_com_timeout_levanta_indisponivel():
    respx.post(BUBBLE_LOGIN_URL).mock(side_effect=httpx.TimeoutException("tempo esgotado"))

    with pytest.raises(BubbleIndisponivel):
        autenticar_no_bubble("usuaria@example.com", "senha-correta")


@respx.mock
def test_autenticar_no_bubble_com_resposta_nao_json_levanta_indisponivel():
    respx.post(BUBBLE_LOGIN_URL).mock(return_value=httpx.Response(200, text="not json"))

    with pytest.raises(BubbleIndisponivel):
        autenticar_no_bubble("usuaria@example.com", "senha-correta")


@respx.mock
def test_autenticar_no_bubble_com_formato_totalmente_inesperado_levanta_indisponivel():
    respx.post(BUBBLE_LOGIN_URL).mock(
        return_value=httpx.Response(
            500,
            json={"algum_campo": "que não é nenhum dos formatos documentados"},
        )
    )

    with pytest.raises(BubbleIndisponivel):
        autenticar_no_bubble("usuaria@example.com", "senha-correta")


def test_autenticar_no_bubble_sem_url_configurada_levanta_indisponivel_sem_chamar_rede(monkeypatch):
    monkeypatch.setattr("app.bubble_client.BUBBLE_LOGIN_URL", None)

    with respx.mock:
        with pytest.raises(BubbleIndisponivel):
            autenticar_no_bubble("usuaria@example.com", "senha-correta")


def test_autenticar_no_bubble_sem_api_secret_configurado_levanta_indisponivel_sem_chamar_rede(monkeypatch):
    monkeypatch.setattr("app.bubble_client.BUBBLE_API_SECRET", None)

    with respx.mock:
        with pytest.raises(BubbleIndisponivel):
            autenticar_no_bubble("usuaria@example.com", "senha-correta")
