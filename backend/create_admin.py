"""Cria (ou promove) o usuário admin do sistema.

Uso: ./venv/Scripts/python.exe create_admin.py
"""

from datetime import datetime, timezone

from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import User

USERNAME = "admin"
SENHA = "Adm200726##"
NOME = "Administrador"


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == USERNAME).first()
        if user:
            user.hashed_password = hash_password(SENHA)
            user.is_admin = True
            user.senha_alterada_em = datetime.now(timezone.utc)
            db.commit()
            print(f"Usuário '{USERNAME}' já existia, senha e permissão de admin atualizadas.")
            return

        user = User(
            username=USERNAME,
            nome=NOME,
            hashed_password=hash_password(SENHA),
            is_admin=True,
            senha_alterada_em=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        print(f"Usuário admin criado: username='{USERNAME}' senha='{SENHA}'")
    finally:
        db.close()


if __name__ == "__main__":
    main()
