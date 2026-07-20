import os
from datetime import datetime, timedelta, timezone

import bcrypt
from dotenv import load_dotenv
from jose import JWTError, jwt

load_dotenv()

SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY não está definido. Configure essa variável em backend/.env antes de iniciar o servidor."
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h

# bcrypt trunca/rejeita senhas acima de 72 bytes (não caracteres — unicode
# multibyte conta mais de 1 byte por caractere). Validar isso na borda da API
# evita um ValueError não tratado (500) vindo do hash_password/verify_password.
SENHA_MAXIMA_BYTES = 72

# Hash de um valor fixo, calculado uma vez, usado só para manter o tempo de
# resposta do login constante quando o usuário não existe (ver login() em
# routers/auth.py) — sem isso, dá pra descobrir por timing se um username
# existe (verify_password/bcrypt só roda quando o usuário é encontrado).
_HASH_TEMPO_CONSTANTE = bcrypt.hashpw(b"tempo-constante-nao-e-uma-senha-real", bcrypt.gensalt()).decode("utf-8")


def senha_excede_limite_bcrypt(senha: str) -> bool:
    return len(senha.encode("utf-8")) > SENHA_MAXIMA_BYTES


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str | None) -> bool:
    if senha_excede_limite_bcrypt(password):
        return False
    return bcrypt.checkpw(password.encode("utf-8"), (hashed or _HASH_TEMPO_CONSTANTE).encode("utf-8"))


def agora_sem_microssegundos() -> datetime:
    """`iat` do JWT perde a precisão de microssegundos ao ser codificado (o jose
    trunca pra segundos inteiros). Se `senha_alterada_em` guardar microssegundos,
    um token emitido no mesmo segundo da troca — mas alguns milissegundos depois
    — pode ser invalidado por engano. Truncar aqui também elimina essa corrida."""
    return datetime.now(timezone.utc).replace(microsecond=0)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    agora = datetime.now(timezone.utc)
    expire = agora + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"iat": agora, "exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
