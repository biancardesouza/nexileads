"""Sobe o backend real (FastAPI/uvicorn) para os testes E2E do Playwright,
com as duas dependências externas do backend (login no Bubble e consulta de
CNPJ na BrasilAPI) interceptadas via respx — ver bubble_mock.py.

Uso: `python -m tests_e2e.server`, disparado pelo `webServer` do Playwright em
frontend/playwright.config.js. Não é pensado pra ser rodado manualmente.
"""

import os
from pathlib import Path

# Precisa ser definido ANTES de qualquer import de app.* — app/auth.py levanta
# RuntimeError no import se JWT_SECRET_KEY não estiver no ambiente (mesmo
# motivo do backend/tests/conftest.py).
os.environ.setdefault("JWT_SECRET_KEY", "e2e-test-secret-key-com-pelo-menos-32-bytes")
os.environ.setdefault("BUBBLE_LOGIN_URL", "https://example.bubbleapps.io/version-e2e/api/1.1/wf/login")
os.environ.setdefault("BUBBLE_API_SECRET", "e2e-test-api-secret")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:4173")
os.environ.setdefault("COOKIE_SECURE", "false")

# Banco descartável e dedicado — recriado do zero a cada execução pra nenhum
# teste depender de estado deixado pela rodada anterior.
_DB_PATH = Path(__file__).resolve().parent.parent / "e2e_nexileads.db"
_DB_PATH.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH.as_posix()}"

import respx  # noqa: E402
import uvicorn  # noqa: E402

from tests_e2e.bubble_mock import registrar_mocks  # noqa: E402

respx.mock.start()
registrar_mocks()

# Banco descartável de E2E, à parte do histórico de migrações do Alembic (que
# agora é quem cria o schema em dev/produção — ver app/main.py) — igual ao
# padrão já usado em backend/tests/conftest.py para os testes de integração.
# `import app.models` primeiro é essencial: sem isso Base.metadata não tem
# nenhuma tabela registrada ainda (as classes só se registram quando o módulo
# é importado) e o create_all abaixo não criaria nada.
import app.models  # noqa: F401,E402
from app.database import Base, engine  # noqa: E402

Base.metadata.create_all(bind=engine)

from app.main import app  # noqa: E402  (só depois das env vars + mock ativo)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
