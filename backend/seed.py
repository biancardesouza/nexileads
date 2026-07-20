"""Popula o banco com um usuário de teste e os leads de exemplo.

Uso: ./venv/Scripts/python.exe seed.py
"""

from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Lead, RegistroLigacao, User

USERNAME = "mariana"
SENHA = "123456"
NOME = "Mariana Costa"

LEADS_EXEMPLO = [
    {
        "razao_social": "Comércio de Alimentos Boa Safra Ltda",
        "cnpj": "12.345.678/0001-90",
        "uf": "SP",
        "municipio": "Campinas",
        "telefone": "(19) 98123-4521",
        "email": "contato@boasafra.com.br",
        "segmento": "Comércio varejista",
        "status": "atendeu",
        "registros": [
            {"status": "atendeu", "nota": "Falei com a Renata (financeiro). Pediu retorno na próxima semana."},
            {"status": "nao_atendeu", "nota": "Ninguém atendeu, tentar de novo à tarde."},
        ],
    },
    {
        "razao_social": "Metalúrgica Ferro & Cia Indústria Ltda",
        "cnpj": "98.765.432/0001-10",
        "uf": "MG",
        "municipio": "Contagem",
        "telefone": "(31) 3221-7788",
        "email": "comercial@ferroecia.com.br",
        "segmento": "Indústria",
        "status": "invalido",
        "registros": [
            {"status": "invalido", "nota": "Número não existe mais / linha desativada."},
        ],
    },
    {
        "razao_social": "TechFlow Soluções em Software Ltda",
        "cnpj": "45.112.233/0001-77",
        "uf": "SP",
        "municipio": "São Paulo",
        "telefone": "(11) 91234-5566",
        "email": "vendas@techflow.com.br",
        "segmento": "Tecnologia",
        "status": "sem_contato",
        "registros": [],
    },
    {
        "razao_social": "Construtora Horizonte Verde Ltda",
        "cnpj": "20.998.111/0001-33",
        "uf": "PR",
        "municipio": "Curitiba",
        "telefone": "(41) 3355-9090",
        "email": "atendimento@horizonteverde.com.br",
        "segmento": "Serviços",
        "status": "nao_atendeu",
        "registros": [
            {"status": "nao_atendeu", "nota": "Caixa postal nas duas tentativas de hoje."},
        ],
    },
]


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == USERNAME).first()
        if user:
            print(f"Usuário '{USERNAME}' já existe (id={user.id}), pulando seed.")
            return

        user = User(username=USERNAME, nome=NOME, hashed_password=hash_password(SENHA))
        db.add(user)
        db.flush()

        for dados in LEADS_EXEMPLO:
            registros = dados.pop("registros")
            lead = Lead(owner_id=user.id, **dados)
            db.add(lead)
            db.flush()
            for r in registros:
                db.add(RegistroLigacao(lead_id=lead.id, **r))

        db.commit()
        print(f"Usuário criado: username='{USERNAME}' senha='{SENHA}'")
        print(f"{len(LEADS_EXEMPLO)} leads de exemplo adicionados.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
