import os

# Precisa ser definido ANTES de qualquer import de app.* — app/auth.py levanta
# RuntimeError no import se JWT_SECRET_KEY não estiver no ambiente.
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-com-pelo-menos-32-bytes-de-comprimento")
os.environ.setdefault("BUBBLE_LOGIN_URL", "https://example.bubbleapps.io/version-test/api/1.1/wf/login")
os.environ.setdefault("BUBBLE_API_SECRET", "test-api-secret")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import rate_limit
from app.auth import TOKEN_COOKIE_NAME, create_access_token
from app.database import Base
from app.dependencies import get_db
from app.main import app
from app.models import User


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def SessionTeste(db_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


@pytest.fixture()
def db_session(SessionTeste):
    session = SessionTeste()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(SessionTeste):
    def override_get_db():
        db = SessionTeste()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_rate_limit():
    rate_limit._falhas.clear()
    yield
    rate_limit._falhas.clear()


@pytest.fixture()
def usuario(db_session):
    user = User(
        username="usuaria@example.com",
        nome="Usuária Teste",
        hashed_password="placeholder-nao-verificado",
        bubble_user_id="bubble-user-1",
        email="usuaria@example.com",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def auth_headers(client, usuario):
    """A autenticação agora é via cookie httpOnly, não header — esta fixture
    seta o cookie diretamente no jar do `client` (imitando o que o navegador
    faria depois de um /auth/login) e devolve um dict vazio, mantido só pra
    não precisar mudar todas as chamadas `client.get(url, headers=auth_headers)`
    já escritas nos testes (passar headers={} é inofensivo)."""
    token = create_access_token({"sub": usuario.username})
    client.cookies.set(TOKEN_COOKIE_NAME, token)
    return {}
