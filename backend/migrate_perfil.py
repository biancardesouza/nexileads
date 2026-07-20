"""Adiciona as colunas de perfil (email, telefone, foto_url) na tabela users
sem apagar os dados existentes.

Uso: ./venv/Scripts/python.exe migrate_perfil.py
"""

from sqlalchemy import inspect, text

from app.database import engine

NOVAS_COLUNAS = {
    "email": "TEXT",
    "telefone": "TEXT",
    "foto_url": "TEXT",
}


def main():
    inspector = inspect(engine)
    colunas_atuais = {c["name"] for c in inspector.get_columns("users")}

    with engine.begin() as conn:
        for nome, tipo in NOVAS_COLUNAS.items():
            if nome in colunas_atuais:
                print(f"coluna '{nome}' já existe, pulando")
                continue
            conn.execute(text(f"ALTER TABLE users ADD COLUMN {nome} {tipo}"))
            print(f"coluna '{nome}' adicionada")


if __name__ == "__main__":
    main()
