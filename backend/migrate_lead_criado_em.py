"""Adiciona a coluna criado_em na tabela leads sem apagar os dados
existentes. As linhas já existentes recebem o timestamp atual, já que não
temos como saber quando foram criadas de verdade — isso só afeta o lembrete
de follow-up (leads antigos não vão parecer "recém-criados" pra sempre, só
até passar o prazo normal de novo).

Uso: ./venv/Scripts/python.exe migrate_lead_criado_em.py
"""

from sqlalchemy import inspect, text

from app.database import engine


def main():
    inspector = inspect(engine)
    colunas_atuais = {c["name"] for c in inspector.get_columns("leads")}

    if "criado_em" in colunas_atuais:
        print("coluna 'criado_em' já existe, pulando")
        return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE leads ADD COLUMN criado_em TIMESTAMP"))
        conn.execute(text("UPDATE leads SET criado_em = CURRENT_TIMESTAMP WHERE criado_em IS NULL"))
    print("coluna 'criado_em' adicionada e preenchida")


if __name__ == "__main__":
    main()
