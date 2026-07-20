"""Restaura o banco (faro.db) a partir de um backup criado pelo
backup_banco.py.

IMPORTANTE: pare o backend antes de rodar isso, e reinicie depois — restaurar
com o servidor no ar pode deixar as conexões já abertas com dados
inconsistentes.

Por segurança, o banco atual é salvo em backend/backups/ antes de ser
sobrescrito, então mesmo restaurando o backup errado dá pra voltar atrás.

Uso:
  ./venv/Scripts/python.exe restaurar_backup.py            (lista os backups disponíveis)
  ./venv/Scripts/python.exe restaurar_backup.py <arquivo>   (restaura o backup escolhido)
"""

import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "faro.db"
BACKUPS_DIR = Path(__file__).parent / "backups"


def listar_backups():
    backups = sorted(BACKUPS_DIR.glob("faro_*.db"), reverse=True)
    if not backups:
        print(f"Nenhum backup encontrado em {BACKUPS_DIR}")
        return
    print("Backups disponíveis:")
    for b in backups:
        print(f"  {b.name}")
    print("\nUso: ./venv/Scripts/python.exe restaurar_backup.py <nome_do_arquivo>")


def main():
    if len(sys.argv) < 2:
        listar_backups()
        return

    origem = BACKUPS_DIR / sys.argv[1]
    if not origem.exists():
        print(f"Backup '{sys.argv[1]}' não encontrado em {BACKUPS_DIR}")
        listar_backups()
        return

    BACKUPS_DIR.mkdir(exist_ok=True)
    if DB_PATH.exists():
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        seguranca = BACKUPS_DIR / f"antes_de_restaurar_{timestamp}.db"
        shutil.copy2(DB_PATH, seguranca)
        print(f"Banco atual salvo em '{seguranca.name}' antes de sobrescrever, por segurança.")

    conn_origem = sqlite3.connect(origem)
    conn_destino = sqlite3.connect(DB_PATH)
    with conn_destino:
        conn_origem.backup(conn_destino)
    conn_origem.close()
    conn_destino.close()

    print(f"Banco restaurado a partir de '{origem.name}'.")
    print("Reinicie o backend agora pra usar os dados restaurados.")


if __name__ == "__main__":
    main()
