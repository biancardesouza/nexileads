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

# Limite por IP é mais alto que o por e-mail de propósito: um IP pode ser
# compartilhado por várias pessoas de verdade (NAT/proxy corporativo), então
# um limite igual ao de e-mail bloquearia usuários legítimos por causa de
# erros de digitação de outra pessoa na mesma rede. Ainda assim, um limite
# existe pra dificultar varredura de credenciais (testar muitos e-mails
# diferentes) a partir de um mesmo IP.
LIMITE_IP = 20

_falhas: dict[str, list[datetime]] = defaultdict(list)


def _tentativas_recentes(chave: str) -> list[datetime]:
    agora = datetime.now(timezone.utc)
    recentes = [t for t in _falhas[chave] if agora - t < JANELA]
    _falhas[chave] = recentes
    return recentes


def bloqueado(chave: str, limite: int = LIMITE) -> bool:
    return len(_tentativas_recentes(chave)) >= limite


def registrar_falha(chave: str) -> None:
    recentes = _tentativas_recentes(chave)
    recentes.append(datetime.now(timezone.utc))
    _falhas[chave] = recentes


def limpar(chave: str) -> None:
    _falhas.pop(chave, None)
