import sqlite3
from datetime import datetime, timedelta

import backup_banco


def _criar_banco_sqlite(caminho, tabela="dados", valor="original"):
    """Cria um arquivo sqlite válido e mínimo, com uma tabela/linha simples."""
    conn = sqlite3.connect(caminho)
    conn.execute(f"CREATE TABLE {tabela} (valor TEXT)")
    conn.execute(f"INSERT INTO {tabela} (valor) VALUES (?)", (valor,))
    conn.commit()
    conn.close()


def test_main_sem_banco_nao_faz_nada(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "nexileads.db"
    backups_dir = tmp_path / "backups"
    monkeypatch.setattr(backup_banco, "DB_PATH", db_path)
    monkeypatch.setattr(backup_banco, "BACKUPS_DIR", backups_dir)

    assert not db_path.exists()

    backup_banco.main()

    saida = capsys.readouterr().out
    assert "não encontrado" in saida.lower()
    # Nada deve ter sido criado.
    assert not backups_dir.exists()


def test_main_cria_backup_valido(tmp_path, monkeypatch):
    db_path = tmp_path / "nexileads.db"
    backups_dir = tmp_path / "backups"
    _criar_banco_sqlite(db_path)

    monkeypatch.setattr(backup_banco, "DB_PATH", db_path)
    monkeypatch.setattr(backup_banco, "BACKUPS_DIR", backups_dir)

    backup_banco.main()

    assert backups_dir.exists()
    encontrados = list(backups_dir.glob("nexileads_*.db"))
    assert len(encontrados) == 1

    # O arquivo gerado deve ser um banco sqlite válido e conter os dados
    # copiados do banco de origem.
    conn = sqlite3.connect(encontrados[0])
    linhas = conn.execute("SELECT valor FROM dados").fetchall()
    conn.close()
    assert linhas == [("original",)]


def test_main_remove_backups_antigos_mas_mantem_recentes(tmp_path, monkeypatch):
    db_path = tmp_path / "nexileads.db"
    backups_dir = tmp_path / "backups"
    _criar_banco_sqlite(db_path)
    backups_dir.mkdir()

    monkeypatch.setattr(backup_banco, "DB_PATH", db_path)
    monkeypatch.setattr(backup_banco, "BACKUPS_DIR", backups_dir)

    # Backup antigo (mais de RETENCAO_DIAS) deve ser removido.
    antigo = backups_dir / "nexileads_antigo.db"
    _criar_banco_sqlite(antigo, valor="antigo")
    mtime_antigo = (datetime.now() - timedelta(days=backup_banco.RETENCAO_DIAS + 5)).timestamp()
    import os

    os.utime(antigo, (mtime_antigo, mtime_antigo))

    # Backup recente (dentro do prazo) deve permanecer.
    recente = backups_dir / "nexileads_recente.db"
    _criar_banco_sqlite(recente, valor="recente")
    mtime_recente = (datetime.now() - timedelta(days=1)).timestamp()
    os.utime(recente, (mtime_recente, mtime_recente))

    backup_banco.main()

    assert not antigo.exists()
    assert recente.exists()

    # E o novo backup criado por main() também deve estar presente.
    novos = [
        p
        for p in backups_dir.glob("nexileads_*.db")
        if p.name not in ("nexileads_antigo.db", "nexileads_recente.db")
    ]
    assert len(novos) == 1
