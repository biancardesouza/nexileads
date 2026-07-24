from app.dependencies import get_db


def test_get_db_gera_e_fecha_sessao():
    gerador = get_db()
    sessao = next(gerador)
    assert sessao is not None

    fechou = False
    original_close = sessao.close

    def close_espiao():
        nonlocal fechou
        fechou = True
        original_close()

    sessao.close = close_espiao

    gerador.close()
    assert fechou
