from apscheduler.triggers.interval import IntervalTrigger

from app import scheduler


def test_iniciar_registra_job_de_limpeza_com_intervalo_de_30_dias():
    scheduler.iniciar()
    try:
        assert scheduler._scheduler.running

        jobs = scheduler._scheduler.get_jobs()
        assert len(jobs) == 1

        job = jobs[0]
        assert job.id == "limpeza_cache_cnpj"
        assert isinstance(job.trigger, IntervalTrigger)
        assert job.trigger.interval.days == scheduler.INTERVALO_DIAS
    finally:
        scheduler.parar()


def test_parar_desliga_o_scheduler():
    scheduler.iniciar()

    scheduler.parar()

    assert scheduler._scheduler is None


def test_parar_sem_scheduler_iniciado_nao_da_erro():
    scheduler._scheduler = None
    scheduler.parar()
    assert scheduler._scheduler is None
