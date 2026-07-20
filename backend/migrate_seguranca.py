"""Adiciona a coluna senha_alterada_em na tabela users sem apagar os dados
existentes. As linhas já existentes recebem o timestamp atual como valor
inicial — na prática isso invalida qualquer token emitido antes da migração,
o que é o comportamento esperado ao reforçar a segurança.

Uso: ./venv/Scripts/python.exe migrate_seguranca.py
"""

from sqlalchemy import inspect, text

from app.database import engine


def main():
    inspector = inspect(engine)
    colunas_atuais = {c["name"] for c in inspector.get_columns("users")}

    if "senha_alterada_em" in colunas_atuais:
        print("coluna 'senha_alterada_em' já existe, pulando")
        return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN senha_alterada_em TIMESTAMP"))
        conn.execute(text("UPDATE users SET senha_alterada_em = CURRENT_TIMESTAMP WHERE senha_alterada_em IS NULL"))
    print("coluna 'senha_alterada_em' adicionada e preenchida")


if __name__ == "__main__":
    main()
