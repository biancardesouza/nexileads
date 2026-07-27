import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Em produção, DATABASE_URL aponta pro Postgres. Sem essa variável
# (dev local), continua usando o arquivo SQLite de sempre.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./nexileads.db")
# Render/Heroku fornecem a URL com o esquema legado "postgres://", que o
# SQLAlchemy 1.4+ não reconhece mais como dialeto (só aceita "postgresql://").
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
