import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv

from alembic import context

# backend/ (pai de alembic/) precisa estar no sys.path pra importar `app.*`
# quando o alembic roda como `alembic upgrade head` a partir de backend/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Mesmo padrão de app/auth.py e app/bubble_client.py — carrega DATABASE_URL de
# um .env local se existir, antes de app.database ler a variável de ambiente.
load_dotenv()

import app.models  # noqa: F401,E402  (efeito colateral: registra as classes em Base.metadata)
from app.database import Base, engine  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Reusa a mesma engine do app (app/database.py) em vez de duplicar a lógica
# de DATABASE_URL/sqlite-vs-postgres aqui no alembic.ini — uma única fonte de
# verdade pra como o app se conecta ao banco.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=str(engine.url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
