"""Roda a limpeza do cache de CNPJ (limpar_dados_antigos.py) periodicamente,
dentro do próprio processo do backend — evita depender de o PC de alguém
estar ligado (Task Scheduler do Windows) ou de um serviço agendado à parte
(Render Cron Job é um recurso pago separado; isso aqui não custa nada a mais).

Funciona igual em qualquer banco (usa SessionLocal/SQLAlchemy via
limpar_dados_antigos.main, sem nada específico de SQLite) — diferente do
backup do banco, que hoje só sabe fazer backup de SQLite local (ver
backup_banco.py) e por isso não cobre a produção (Postgres no Neon, que já
tem seu próprio backup/point-in-time recovery nativo).
"""

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

import limpar_dados_antigos

INTERVALO_DIAS = 30  # mesma cadência já sugerida no docstring do próprio script

_scheduler: BackgroundScheduler | None = None


def iniciar() -> None:
    global _scheduler
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        limpar_dados_antigos.main,
        "interval",
        days=INTERVALO_DIAS,
        id="limpeza_cache_cnpj",
        # Roda uma vez já na subida, não só depois de 30 dias — barato (é só
        # um DELETE que não faz nada se não há nada pra limpar).
        next_run_time=datetime.now(),
    )
    _scheduler.start()


def parar() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
