import importlib

import app.database
from sqlalchemy import text


def test_sqlite_url_usa_check_same_thread_false(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    importlib.reload(app.database)

    try:
        assert app.database.DATABASE_URL.startswith("sqlite")
        assert app.database.connect_args == {"check_same_thread": False}
        assert app.database.engine.url.drivername.startswith("sqlite")

        # Confirma que a sessão funciona sem erro de threading.
        session = app.database.SessionLocal()
        try:
            resultado = session.execute(text("SELECT 1")).scalar()
            assert resultado == 1
        finally:
            session.close()
    finally:
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
        importlib.reload(app.database)


def test_postgres_url_nao_usa_connect_args_especial(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
    importlib.reload(app.database)

    try:
        assert app.database.DATABASE_URL == "postgresql://user:pass@localhost/db"
        assert app.database.connect_args == {}
        assert app.database.engine.url.drivername == "postgresql"
    finally:
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
        importlib.reload(app.database)


def test_estado_do_modulo_e_restaurado_apos_testes():
    # Garante que, independente da ordem de execução, o módulo termina no
    # estado esperado pelo resto da suíte (sqlite em memória).
    assert app.database.DATABASE_URL == "sqlite:///:memory:"
    assert app.database.connect_args == {"check_same_thread": False}
