"""Cria uma cópia de segurança do banco (nexileads.db) em backend/backups/.

Usa a API de backup do próprio SQLite (Connection.backup), não uma cópia
crua do arquivo — isso evita corromper o backup caso o banco esteja em uso
(o backend pode continuar rodando normalmente enquanto isso roda).

Backups com mais de RETENCAO_DIAS são apagados automaticamente a cada
execução, pra não crescer sem limite.

Uso: ./venv/Scripts/python.exe backup_banco.py
Rode periodicamente (ex: uma vez por dia) via agendador de tarefas do
Windows, se quiser que isso aconteça sozinho.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "nexileads.db"
BACKUPS_DIR = Path(__file__).parent / "backups"
RETENCAO_DIAS = 30


def main():
    if not DB_PATH.exists():
        print(f"Banco não encontrado em {DB_PATH}")
        return

    BACKUPS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    destino = BACKUPS_DIR / f"nexileads_{timestamp}.db"

    origem = sqlite3.connect(DB_PATH)
    backup = sqlite3.connect(destino)
    with backup:
        origem.backup(backup)
    origem.close()
    backup.close()
    print(f"Backup criado: {destino}")

    limite = datetime.now() - timedelta(days=RETENCAO_DIAS)
    removidos = 0
    for padrao in ("nexileads_*.db", "faro_*.db"):
        for arquivo in BACKUPS_DIR.glob(padrao):
            if datetime.fromtimestamp(arquivo.stat().st_mtime) < limite:
                arquivo.unlink()
                removidos += 1
    if removidos:
        print(f"{removidos} backup(s) com mais de {RETENCAO_DIAS} dias removido(s)")


if __name__ == "__main__":
    main()
