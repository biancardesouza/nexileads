import sqlite3
import sys

import restaurar_backup


def _criar_banco_sqlite(caminho, tabela="dados", valor="original"):
    """Cria um arquivo sqlite válido e mínimo, com uma tabela/linha simples."""
    conn = sqlite3.connect(caminho)
    conn.execute(f"CREATE TABLE {tabela} (valor TEXT)")
    conn.execute(f"INSERT INTO {tabela} (valor) VALUES (?)", (valor,))
    conn.commit()
    conn.close()


def _ler_valor(caminho, tabela="dados"):
    conn = sqlite3.connect(caminho)
    linhas = conn.execute(f"SELECT valor FROM {tabela}").fetchall()
    conn.close()
    return linhas


def test_listar_backups_pasta_inexistente_nao_levanta_erro(tmp_path, monkeypatch, capsys):
    backups_dir = tmp_path / "backups"
    monkeypatch.setattr(restaurar_backup, "BACKUPS_DIR", backups_dir)

    assert not backups_dir.exists()
    restaurar_backup.listar_backups()

    saida = capsys.readouterr().out
    assert "nenhum backup" in saida.lower()


def test_listar_backups_pasta_vazia_nao_levanta_erro(tmp_path, monkeypatch, capsys):
    backups_dir = tmp_path / "backups"
    backups_dir.mkdir()
    monkeypatch.setattr(restaurar_backup, "BACKUPS_DIR", backups_dir)

    restaurar_backup.listar_backups()

    saida = capsys.readouterr().out
    assert "nenhum backup" in saida.lower()


def test_listar_backups_com_arquivos_lista_nomes(tmp_path, monkeypatch, capsys):
    backups_dir = tmp_path / "backups"
    backups_dir.mkdir()
    _criar_banco_sqlite(backups_dir / "nexileads_um.db")
    _criar_banco_sqlite(backups_dir / "faro_dois.db")
    monkeypatch.setattr(restaurar_backup, "BACKUPS_DIR", backups_dir)

    restaurar_backup.listar_backups()

    saida = capsys.readouterr().out
    assert "nexileads_um.db" in saida
    assert "faro_dois.db" in saida


def test_main_sem_argumentos_lista_backups(tmp_path, monkeypatch, capsys):
    backups_dir = tmp_path / "backups"
    db_path = tmp_path / "nexileads.db"
    monkeypatch.setattr(restaurar_backup, "BACKUPS_DIR", backups_dir)
    monkeypatch.setattr(restaurar_backup, "DB_PATH", db_path)
    monkeypatch.setattr(sys, "argv", ["restaurar_backup.py"])

    restaurar_backup.main()

    saida = capsys.readouterr().out
    assert "nenhum backup" in saida.lower()
    assert not db_path.exists()


def test_main_arquivo_inexistente_avisa_e_nao_altera_db(tmp_path, monkeypatch, capsys):
    backups_dir = tmp_path / "backups"
    backups_dir.mkdir()
    db_path = tmp_path / "nexileads.db"
    _criar_banco_sqlite(db_path, valor="atual")
    conteudo_antes = db_path.read_bytes()

    monkeypatch.setattr(restaurar_backup, "BACKUPS_DIR", backups_dir)
    monkeypatch.setattr(restaurar_backup, "DB_PATH", db_path)
    monkeypatch.setattr(sys, "argv", ["restaurar_backup.py", "nao_existe.db"])

    restaurar_backup.main()

    saida = capsys.readouterr().out
    assert "não encontrado" in saida.lower()
    assert db_path.read_bytes() == conteudo_antes


def test_main_restaura_backup_valido_e_salva_seguranca(tmp_path, monkeypatch):
    backups_dir = tmp_path / "backups"
    backups_dir.mkdir()
    db_path = tmp_path / "nexileads.db"

    # Banco "atual" com uma tabela/valor.
    _criar_banco_sqlite(db_path, valor="atual")

    # Backup com uma tabela/valor diferente.
    backup_path = backups_dir / "nexileads_teste.db"
    _criar_banco_sqlite(backup_path, valor="do_backup")

    monkeypatch.setattr(restaurar_backup, "BACKUPS_DIR", backups_dir)
    monkeypatch.setattr(restaurar_backup, "DB_PATH", db_path)
    monkeypatch.setattr(sys, "argv", ["restaurar_backup.py", "nexileads_teste.db"])

    restaurar_backup.main()

    # O banco atual agora deve refletir o conteúdo do backup restaurado.
    assert _ler_valor(db_path) == [("do_backup",)]

    # E uma cópia de segurança do banco antigo deve ter sido criada.
    seguranca = list(backups_dir.glob("antes_de_restaurar_*.db"))
    assert len(seguranca) == 1
    assert _ler_valor(seguranca[0]) == [("atual",)]
