import pytest
from fastapi import HTTPException

from app.auth import create_access_token
from app.dependencies import get_current_user
from app.models import User


def test_get_current_user_com_token_valido_retorna_usuario(db_session, usuario):
    token = create_access_token({"sub": usuario.username})

    user = get_current_user(token=token, db=db_session)

    assert user.id == usuario.id
    assert user.username == usuario.username


def test_get_current_user_com_token_invalido_levanta_401(db_session):
    with pytest.raises(HTTPException) as exc:
        get_current_user(token="token-invalido-e-corrompido", db=db_session)

    assert exc.value.status_code == 401


def test_get_current_user_com_token_sem_sub_levanta_401(db_session):
    token = create_access_token({"outro_campo": "sem-sub-aqui"})

    with pytest.raises(HTTPException) as exc:
        get_current_user(token=token, db=db_session)

    assert exc.value.status_code == 401


def test_get_current_user_com_username_inexistente_levanta_401(db_session):
    token = create_access_token({"sub": "usuario-que-nao-existe@example.com"})

    with pytest.raises(HTTPException) as exc:
        get_current_user(token=token, db=db_session)

    assert exc.value.status_code == 401


def test_get_current_user_nao_e_afetado_por_outros_usuarios(db_session, usuario):
    outro = User(
        username="outra@example.com",
        nome="Outra Usuária",
        hashed_password="placeholder-nao-verificado",
        bubble_user_id="bubble-user-2",
        email="outra@example.com",
    )
    db_session.add(outro)
    db_session.commit()
    db_session.refresh(outro)

    token = create_access_token({"sub": outro.username})

    user = get_current_user(token=token, db=db_session)

    assert user.id == outro.id
    assert user.id != usuario.id
