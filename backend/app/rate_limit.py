"""Bloqueio simples de força bruta no login, em memória (por processo).

Guarda os horários das últimas tentativas falhas por username. Depois de
LIMITE falhas dentro da JANELA, novas tentativas são bloqueadas até a janela
"esfriar". Reinicia junto com o processo do servidor — suficiente pro porte
deste app, sem precisar de Redis ou tabela no banco.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

JANELA = timedelta(minutes=15)
LIMITE = 5

_falhas: dict[str, list[datetime]] = defaultdict(list)


def _tentativas_recentes(chave: str) -> list[datetime]:
    agora = datetime.now(timezone.utc)
    recentes = [t for t in _falhas[chave] if agora - t < JANELA]
    _falhas[chave] = recentes
    return recentes


def bloqueado(chave: str) -> bool:
    return len(_tentativas_recentes(chave)) >= LIMITE


def registrar_falha(chave: str) -> None:
    recentes = _tentativas_recentes(chave)
    recentes.append(datetime.now(timezone.utc))
    _falhas[chave] = recentes


def limpar(chave: str) -> None:
    _falhas.pop(chave, None)
