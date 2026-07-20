"""Adiciona a coluna is_admin na tabela users sem apagar os dados existentes.

Uso: ./venv/Scripts/python.exe migrate_admin.py
"""

from sqlalchemy import inspect, text

from app.database import engine


def main():
    inspector = inspect(engine)
    colunas_atuais = {c["name"] for c in inspector.get_columns("users")}

    if "is_admin" in colunas_atuais:
        print("coluna 'is_admin' já existe, pulando")
        return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL"))
    print("coluna 'is_admin' adicionada")


if __name__ == "__main__":
    main()
