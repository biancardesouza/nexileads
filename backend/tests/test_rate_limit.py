from datetime import datetime, timedelta, timezone

from app import rate_limit
from app.rate_limit import JANELA, LIMITE, bloqueado, limpar, registrar_falha


def test_nao_bloqueado_sem_tentativas():
    assert bloqueado("usuario-sem-tentativas") is False


def test_nao_bloqueado_com_limite_menos_uma_falha():
    chave = "usuario-quase-limite"

    for _ in range(LIMITE - 1):
        registrar_falha(chave)

    assert bloqueado(chave) is False


def test_bloqueado_ao_atingir_limite():
    chave = "usuario-atingiu-limite"

    for _ in range(LIMITE):
        registrar_falha(chave)

    assert bloqueado(chave) is True


def test_janela_expira_e_desbloqueia():
    chave = "usuario-janela-expirada"

    # Todas as falhas fora da janela: não deveriam contar mais.
    antiga = datetime.now(timezone.utc) - JANELA - timedelta(minutes=1)
    rate_limit._falhas[chave] = [antiga for _ in range(LIMITE)]

    assert bloqueado(chave) is False
    assert rate_limit._falhas[chave] == []


def test_limpar_reseta_apenas_a_chave_especificada():
    chave_a = "usuario-a"
    chave_b = "usuario-b"

    for _ in range(LIMITE):
        registrar_falha(chave_a)
        registrar_falha(chave_b)

    assert bloqueado(chave_a) is True
    assert bloqueado(chave_b) is True

    limpar(chave_a)

    # Checa a ausência da chave antes de qualquer outra chamada: `bloqueado()`
    # usa um defaultdict e recria a entrada (vazia) ao ser consultada.
    assert chave_a not in rate_limit._falhas
    assert bloqueado(chave_a) is False
    assert bloqueado(chave_b) is True


def test_limpar_chave_inexistente_nao_levanta_erro():
    limpar("chave-que-nunca-existiu")
