from pathlib import Path

import pytest

from multidb.core import MigrationError, discover_migrations


def make_migration(base: Path, name: str, up: str = "SELECT 1;", down: str = "SELECT 1;") -> Path:
    folder = base / name
    folder.mkdir()
    (folder / "up.sql").write_text(up)
    (folder / "down.sql").write_text(down)
    return folder


def test_sorts_by_numeric_version(tmp_path):
    for name in ("V10__dez", "V2__dois", "V1__um"):
        make_migration(tmp_path, name)

    versions = [m.version for m in discover_migrations(tmp_path)]

    assert versions == [1, 2, 10]


def test_invalid_name_raises(tmp_path):
    make_migration(tmp_path, "V1-sem-underline-duplo")

    with pytest.raises(MigrationError, match="fora do padrão"):
        discover_migrations(tmp_path)


def test_missing_down_sql_raises(tmp_path):
    folder = make_migration(tmp_path, "V1__um")
    (folder / "down.sql").unlink()

    with pytest.raises(MigrationError):
        discover_migrations(tmp_path)


def test_duplicate_version_raises(tmp_path):
    make_migration(tmp_path, "V1__um")
    make_migration(tmp_path, "V1__dois")

    with pytest.raises(MigrationError):
        discover_migrations(tmp_path)


def test_ignores_hidden_files(tmp_path):
    make_migration(tmp_path, "V1__um")
    (tmp_path / ".gitkeep").touch()

    migrations = discover_migrations(tmp_path)

    assert len(migrations) == 1
