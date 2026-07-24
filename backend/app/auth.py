import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY não está definido. Configure essa variável em backend/.env antes de iniciar o servidor."
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h

TOKEN_COOKIE_NAME = "nexileads_token"

# Em produção (Render), frontend e backend ficam em domínios diferentes
# (cross-site) e servem em HTTPS — o cookie precisa de Secure=True e
# SameSite=None pra ser enviado nas chamadas da SPA pro backend (o navegador
# recusa SameSite=None sem Secure). Em dev local os dois rodam em
# http://localhost com portas diferentes, que o navegador trata como
# "same-site" (mesmo host, sem HTTPS) — SameSite=Lax funciona e não exige
# Secure, o que é necessário já que dev local normalmente não tem HTTPS.
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").strip().lower() == "true"
COOKIE_SAMESITE = "none" if COOKIE_SECURE else "lax"


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    agora = datetime.now(timezone.utc)
    expire = agora + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"iat": agora, "exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
