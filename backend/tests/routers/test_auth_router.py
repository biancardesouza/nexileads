import httpx
import respx
from starlette.requests import Request

from app.auth import TOKEN_COOKIE_NAME
from app.bubble_client import BUBBLE_LOGIN_URL
from app.models import User
from app.rate_limit import LIMITE, LIMITE_IP
from app.routers.auth import normalizar_telefone, obter_ip_cliente


# ---------------------------------------------------------------------------
# normalizar_telefone (função pura, testada direto)
# ---------------------------------------------------------------------------


def test_normalizar_telefone_com_11_digitos():
    assert normalizar_telefone("11912345678") == "(11) 91234-5678"


def test_normalizar_telefone_com_11_digitos_ja_formatado():
    assert normalizar_telefone("(11) 91234-5678") == "(11) 91234-5678"


def test_normalizar_telefone_com_10_digitos_telefone_fixo():
    assert normalizar_telefone("1140001000") == "(11) 4000-1000"


def test_normalizar_telefone_com_formato_invalido_retorna_none():
    assert normalizar_telefone("123") is None
    assert normalizar_telefone("119123456789") is None


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


def _resposta_bubble_sucesso(**overrides):
    dados = {
        "id": "bubble-99",
        "email": "nova@x.com",
        "name": "Nova Pessoa",
        "telephone": "11912345678",
        "photo_url": "/uploads/x.jpg",
    }
    dados.update(overrides)
    # bubble_client.autenticar_no_bubble só aceita a resposta interna se ela
    # também tiver "status": "success" — sem isso ele levanta
    # BubbleIndisponivel (ver app/bubble_client.py linha 71).
    dados["status"] = "success"
    return {"status": "success", "response": dados}


def _resposta_bubble_credenciais_invalidas():
    return {
        "statusCode": 400,
        "reason": "INVALID_LOGIN_CREDENTIALS",
        "message": "credenciais inválidas",
    }


@respx.mock
def test_login_usuario_novo_cria_usuario_e_retorna_token(client, db_session):
    respx.post(BUBBLE_LOGIN_URL).mock(
        return_value=httpx.Response(200, json=_resposta_bubble_sucesso())
    )

    resp = client.post("/auth/login", json={"email": "nova@x.com", "password": "senha123"})

    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["nome"] == "Nova Pessoa"
    assert "access_token" not in corpo  # o token não trafega mais no corpo — só via cookie httpOnly

    cookie_header = resp.headers.get("set-cookie", "")
    assert TOKEN_COOKIE_NAME in cookie_header
    assert "HttpOnly" in cookie_header
    assert resp.cookies.get(TOKEN_COOKIE_NAME)

    usuario_criado = db_session.query(User).filter(User.bubble_user_id == "bubble-99").first()
    assert usuario_criado is not None
    assert usuario_criado.email == "nova@x.com"
    assert usuario_criado.nome == "Nova Pessoa"
    assert usuario_criado.telefone == "(11) 91234-5678"
    assert usuario_criado.foto_url == "/uploads/x.jpg"


@respx.mock
def test_login_usuario_ja_existente_nao_duplica_e_atualiza_campos(client, db_session):
    usuario_existente = User(
        username="antiga@x.com",
        nome="Nome Antigo",
        hashed_password="placeholder",
        bubble_user_id="bubble-1",
        email="antiga@x.com",
    )
    db_session.add(usuario_existente)
    db_session.commit()
    id_original = usuario_existente.id

    respx.post(BUBBLE_LOGIN_URL).mock(
        return_value=httpx.Response(
            200,
            json=_resposta_bubble_sucesso(
                id="bubble-1",
                email="antiga@x.com",
                name="Nome Atualizado",
                telephone="11988887777",
                photo_url="/uploads/nova-foto.jpg",
            ),
        )
    )

    resp = client.post("/auth/login", json={"email": "antiga@x.com", "password": "senha123"})

    assert resp.status_code == 200
    # A rota do client roda numa Session diferente (mesma engine): força
    # recarregar do banco em vez de usar o identity map desta Session.
    db_session.expire_all()
    usuarios = db_session.query(User).filter(User.bubble_user_id == "bubble-1").all()
    assert len(usuarios) == 1
    assert usuarios[0].id == id_original
    assert usuarios[0].nome == "Nome Atualizado"
    assert usuarios[0].telefone == "(11) 98888-7777"
    # username não é alterado pela sincronização, só é definido na criação.
    assert usuarios[0].username == "antiga@x.com"


@respx.mock
def test_login_linka_conta_preexistente_por_email_sem_duplicar(client, db_session):
    conta_local = User(
        username="linkavel@x.com",
        nome="Nome Original",
        hashed_password="placeholder",
        bubble_user_id=None,
        email="linkavel@x.com",
    )
    db_session.add(conta_local)
    db_session.commit()
    id_original = conta_local.id

    respx.post(BUBBLE_LOGIN_URL).mock(
        return_value=httpx.Response(
            200,
            json=_resposta_bubble_sucesso(
                id="bubble-777",
                email="linkavel@x.com",
                name="Nome Original",
                telephone=None,
                photo_url=None,
            ),
        )
    )

    resp = client.post("/auth/login", json={"email": "linkavel@x.com", "password": "senha123"})

    assert resp.status_code == 200
    db_session.expire_all()
    usuarios_com_email = (
        db_session.query(User).filter(User.email == "linkavel@x.com").all()
    )
    assert len(usuarios_com_email) == 1
    assert usuarios_com_email[0].id == id_original
    assert usuarios_com_email[0].bubble_user_id == "bubble-777"


@respx.mock
def test_login_sem_telefone_nao_seta_campo(client, db_session):
    respx.post(BUBBLE_LOGIN_URL).mock(
        return_value=httpx.Response(
            200,
            json=_resposta_bubble_sucesso(
                id="bubble-sem-tel", email="semtel@x.com", telephone=None, photo_url=None
            ),
        )
    )

    resp = client.post("/auth/login", json={"email": "semtel@x.com", "password": "senha123"})

    assert resp.status_code == 200
    usuario = db_session.query(User).filter(User.bubble_user_id == "bubble-sem-tel").first()
    assert usuario is not None
    assert usuario.telefone is None


@respx.mock
def test_login_com_telefone_invalido_nao_seta_campo(client, db_session):
    respx.post(BUBBLE_LOGIN_URL).mock(
        return_value=httpx.Response(
            200,
            json=_resposta_bubble_sucesso(
                id="bubble-tel-invalido",
                email="telinvalido@x.com",
                telephone="123",
                photo_url=None,
            ),
        )
    )

    resp = client.post("/auth/login", json={"email": "telinvalido@x.com", "password": "senha123"})

    assert resp.status_code == 200
    usuario = db_session.query(User).filter(User.bubble_user_id == "bubble-tel-invalido").first()
    assert usuario is not None
    assert usuario.telefone is None


@respx.mock
def test_login_credenciais_invalidas_retorna_401_e_repete_401_na_segunda_tentativa(client):
    rota = respx.post(BUBBLE_LOGIN_URL).mock(
        return_value=httpx.Response(200, json=_resposta_bubble_credenciais_invalidas())
    )

    resp1 = client.post("/auth/login", json={"email": "errada@x.com", "password": "senha-errada"})
    resp2 = client.post("/auth/login", json={"email": "errada@x.com", "password": "senha-errada"})

    assert resp1.status_code == 401
    assert resp2.status_code == 401
    assert rota.call_count == 2


@respx.mock
def test_login_bubble_indisponivel_retorna_503(client):
    respx.post(BUBBLE_LOGIN_URL).mock(side_effect=httpx.ConnectError("conexão recusada"))

    resp = client.post("/auth/login", json={"email": "qualquer@x.com", "password": "senha123"})

    assert resp.status_code == 503


@respx.mock
def test_login_bloqueia_por_rate_limit_apos_limite_sem_chamar_bubble(client):
    rota = respx.post(BUBBLE_LOGIN_URL).mock(
        return_value=httpx.Response(200, json=_resposta_bubble_credenciais_invalidas())
    )

    email = "forcabruta@x.com"
    for _ in range(LIMITE):
        resposta = client.post("/auth/login", json={"email": email, "password": "senha-errada"})
        assert resposta.status_code == 401

    assert rota.call_count == LIMITE

    resposta_bloqueada = client.post(
        "/auth/login", json={"email": email, "password": "senha-errada"}
    )

    assert resposta_bloqueada.status_code == 429
    # Nenhuma chamada extra ao Bubble — o bloqueio acontece antes.
    assert rota.call_count == LIMITE


def _fake_request(headers=None, client_host="10.0.0.1"):
    scope = {
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "client": (client_host, 12345) if client_host else None,
    }
    return Request(scope)


def test_obter_ip_cliente_prefere_x_forwarded_for():
    """Atrás do load balancer do Render, request.client.host é o IP do proxy —
    obter_ip_cliente deve preferir o X-Forwarded-For quando presente."""
    request = _fake_request(headers={"x-forwarded-for": "203.0.113.7, 10.0.0.1"})
    assert obter_ip_cliente(request) == "203.0.113.7"


def test_obter_ip_cliente_sem_forwarded_usa_ip_da_conexao_direta():
    request = _fake_request(headers={}, client_host="127.0.0.1")
    assert obter_ip_cliente(request) == "127.0.0.1"


def test_obter_ip_cliente_sem_client_retorna_none():
    request = _fake_request(headers={}, client_host=None)
    assert obter_ip_cliente(request) is None


@respx.mock
def test_login_bloqueia_por_rate_limit_de_ip_mesmo_com_emails_diferentes(client):
    """Varredura de credenciais usando muitos e-mails diferentes a partir do
    mesmo IP também deve ser bloqueada, mesmo que nenhum e-mail individual
    bata no próprio limite (LIMITE=5)."""
    rota = respx.post(BUBBLE_LOGIN_URL).mock(
        return_value=httpx.Response(200, json=_resposta_bubble_credenciais_invalidas())
    )
    ip_fixo = {"x-forwarded-for": "198.51.100.42"}

    for i in range(LIMITE_IP):
        email = f"varredura{i}@x.com"
        resposta = client.post(
            "/auth/login", json={"email": email, "password": "senha-errada"}, headers=ip_fixo
        )
        assert resposta.status_code == 401

    assert rota.call_count == LIMITE_IP

    resposta_bloqueada = client.post(
        "/auth/login",
        json={"email": "mais-um-email-diferente@x.com", "password": "senha-errada"},
        headers=ip_fixo,
    )

    assert resposta_bloqueada.status_code == 429
    assert rota.call_count == LIMITE_IP


@respx.mock
def test_login_rate_limit_de_ip_nao_afeta_ips_diferentes(client):
    rota = respx.post(BUBBLE_LOGIN_URL).mock(
        return_value=httpx.Response(200, json=_resposta_bubble_credenciais_invalidas())
    )

    for i in range(LIMITE_IP):
        client.post(
            "/auth/login",
            json={"email": f"outravarredura{i}@x.com", "password": "senha-errada"},
            headers={"x-forwarded-for": "198.51.100.1"},
        )

    resposta_outro_ip = client.post(
        "/auth/login",
        json={"email": "pessoa-de-verdade@x.com", "password": "senha-errada"},
        headers={"x-forwarded-for": "198.51.100.2"},
    )

    assert resposta_outro_ip.status_code == 401
    assert rota.call_count == LIMITE_IP + 1


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


def test_me_sem_token_retorna_401(client):
    resp = client.get("/auth/me")

    assert resp.status_code == 401


def test_me_com_token_valido_retorna_dados_do_usuario(client, usuario, auth_headers):
    resp = client.get("/auth/me", headers=auth_headers)

    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["username"] == usuario.username
    assert corpo["nome"] == usuario.nome
    assert corpo["email"] == usuario.email


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------


@respx.mock
def test_logout_limpa_o_cookie_e_invalida_a_sessao(client):
    # Loga de verdade (em vez de usar a fixture auth_headers, que injeta o
    # cookie direto no jar do client) pra garantir que o cookie fica com o
    # mesmo escopo (domínio/path) que o Set-Cookie de /auth/logout precisa
    # sobrescrever — só assim o jar do httpx realmente descarta a sessão.
    respx.post(BUBBLE_LOGIN_URL).mock(
        return_value=httpx.Response(200, json=_resposta_bubble_sucesso())
    )
    client.post("/auth/login", json={"email": "nova@x.com", "password": "senha123"})
    assert client.get("/auth/me").status_code == 200

    resp = client.post("/auth/logout")
    assert resp.status_code == 204

    cookie_header = resp.headers.get("set-cookie", "")
    assert TOKEN_COOKIE_NAME in cookie_header
    # delete_cookie expira o cookie no passado — é assim que o navegador sabe
    # que deve descartá-lo, já que sendo httpOnly o front não pode apagá-lo.
    assert "01 Jan 1970" in cookie_header or "Max-Age=0" in cookie_header

    resp_depois = client.get("/auth/me")
    assert resp_depois.status_code == 401


def test_logout_sem_sessao_ativa_nao_da_erro(client):
    resp = client.post("/auth/logout")
    assert resp.status_code == 204
