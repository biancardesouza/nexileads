from datetime import datetime, timedelta, timezone

import jwt

from app.auth import ALGORITHM, SECRET_KEY, create_access_token, decode_access_token


def test_create_access_token_gera_jwt_decodificavel():
    token = create_access_token({"sub": "usuaria@example.com"})

    assert isinstance(token, str)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "usuaria@example.com"


def test_create_access_token_contem_iat_e_exp():
    antes = datetime.now(timezone.utc)
    token = create_access_token({"sub": "usuaria@example.com"})
    depois = datetime.now(timezone.utc)

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert "iat" in payload
    assert "exp" in payload

    iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    assert antes - timedelta(seconds=5) <= iat <= depois + timedelta(seconds=5)
    assert exp > iat


def test_decode_access_token_com_token_valido_retorna_payload():
    token = create_access_token({"sub": "usuaria@example.com", "extra": "valor"})

    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "usuaria@example.com"
    assert payload["extra"] == "valor"


def test_decode_access_token_com_token_malformado_retorna_none():
    assert decode_access_token("isso-nao-eh-um-jwt") is None


def test_decode_access_token_com_token_assinado_com_outra_chave_retorna_none():
    token_invalido = jwt.encode(
        {"sub": "quem-quer-que-seja"}, "chave-errada-mas-com-32-bytes-ok", algorithm=ALGORITHM
    )

    assert decode_access_token(token_invalido) is None


def test_decode_access_token_expirado_retorna_none():
    agora = datetime.now(timezone.utc)
    expirado_ha_1_minuto = agora - timedelta(minutes=1)
    token_expirado = jwt.encode(
        {"sub": "usuaria@example.com", "iat": agora - timedelta(minutes=2), "exp": expirado_ha_1_minuto},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    assert decode_access_token(token_expirado) is None
