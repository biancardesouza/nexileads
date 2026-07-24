from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import limpar_dados_antigos
from app.database import Base
from app.models import CnpjConsulta  # garante que a tabela está registrada no Base.metadata


def _sessionmaker_isolado(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocalIsolado = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr("limpar_dados_antigos.SessionLocal", SessionLocalIsolado)
    return SessionLocalIsolado


def _criar_consulta(cnpj, dias_atras):
    agora = datetime.now(timezone.utc)
    return CnpjConsulta(
        cnpj=cnpj,
        razao_social=f"Empresa {cnpj}",
        uf="SP",
        municipio="São Paulo",
        telefone="11999999999",
        email="contato@example.com",
        segmento="Tecnologia",
        situacao_cadastral="ATIVA",
        fonte="teste",
        consultado_em=agora - timedelta(days=dias_atras),
    )


def test_main_remove_apenas_entradas_com_mais_de_90_dias(monkeypatch, capsys):
    SessionLocalIsolado = _sessionmaker_isolado(monkeypatch)

    session = SessionLocalIsolado()
    recente = _criar_consulta("11111111000191", dias_atras=1)
    antiga_1 = _criar_consulta("22222222000192", dias_atras=91)
    antiga_2 = _criar_consulta("33333333000193", dias_atras=200)
    no_limite = _criar_consulta("44444444000194", dias_atras=89)
    session.add_all([recente, antiga_1, antiga_2, no_limite])
    session.commit()
    session.close()

    limpar_dados_antigos.main()

    saida = capsys.readouterr().out
    assert "2 entrada" in saida

    session = SessionLocalIsolado()
    restantes = {c.cnpj for c in session.query(CnpjConsulta).all()}
    session.close()

    assert restantes == {"11111111000191", "44444444000194"}


def test_main_sem_entradas_antigas_nao_remove_nada(monkeypatch, capsys):
    SessionLocalIsolado = _sessionmaker_isolado(monkeypatch)

    session = SessionLocalIsolado()
    recente = _criar_consulta("55555555000195", dias_atras=1)
    session.add(recente)
    session.commit()
    session.close()

    limpar_dados_antigos.main()

    saida = capsys.readouterr().out
    assert "0 entrada" in saida

    session = SessionLocalIsolado()
    restantes = session.query(CnpjConsulta).count()
    session.close()

    assert restantes == 1
