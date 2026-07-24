import os

from app.main import app


def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_cors_allowed_origins_default_from_env(monkeypatch):
    """allowed_origins em app/main.py é lido do ambiente no import do módulo —
    aqui só garantimos que o valor setado no conftest é o usado pelo middleware
    já registrado (o middleware é configurado uma única vez no import)."""
    assert os.environ["ALLOWED_ORIGINS"] == "http://localhost:5173"
    origins_middleware = next(
        m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"
    )
    assert "http://localhost:5173" in origins_middleware.kwargs["allow_origins"]


def test_routers_registrados(client, auth_headers):
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    resp = client.get("/leads", headers=auth_headers)
    assert resp.status_code == 200


def test_headers_de_seguranca_presentes(client):
    resp = client.get("/api/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert resp.headers["Strict-Transport-Security"] == "max-age=63072000; includeSubDomains"


def test_cors_metodos_e_headers_restritos():
    origins_middleware = next(
        m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"
    )
    assert set(origins_middleware.kwargs["allow_methods"]) == {"GET", "POST", "DELETE"}
    assert set(origins_middleware.kwargs["allow_headers"]) == {"Content-Type"}
