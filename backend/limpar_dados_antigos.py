"""Limpa entradas do cache de CNPJ velhas demais pra ainda servir de cache
de verdade.

Não apaga nada que ainda esteja em uso — só o que já perdeu utilidade.

Uso: ./venv/Scripts/python.exe limpar_dados_antigos.py
Rode periodicamente (ex: uma vez por mês) via agendador de tarefas do
Windows, se quiser que isso aconteça sozinho.
"""

from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models import CnpjConsulta

# Além do prazo de 30 dias que já decide se o cache ainda "vale" pra evitar
# bater na API de novo (ver CNPJ_CACHE_DIAS em routers/leads.py), entradas
# muito mais velhas que isso não têm motivo pra continuar ocupando espaço.
RETENCAO_CACHE_CNPJ_DIAS = 90


def main():
    db = SessionLocal()
    try:
        agora = datetime.now(timezone.utc)

        limite_cache = agora - timedelta(days=RETENCAO_CACHE_CNPJ_DIAS)
        cache_removido = (
            db.query(CnpjConsulta)
            .filter(CnpjConsulta.consultado_em < limite_cache)
            .delete(synchronize_session=False)
        )

        db.commit()
        print(f"{cache_removido} entrada(s) de cache de CNPJ removida(s) (mais de {RETENCAO_CACHE_CNPJ_DIAS} dias)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
