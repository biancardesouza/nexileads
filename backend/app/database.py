import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Em produção (Vercel), DATABASE_URL aponta pro Postgres (Neon) — função
# serverless não tem disco persistente, então SQLite não sobrevive lá. Sem
# essa variável (dev local), continua usando o arquivo SQLite de sempre.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./nexileads.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
