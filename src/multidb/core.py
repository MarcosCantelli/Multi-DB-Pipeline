import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

MIGRATION_DIR_PATTERN = re.compile(r"^V(\d+)__(\w+)$")


class MigrationError(Exception):
    """Erro na estrutura das migrations em disco, detectado antes de tocar no banco."""


@dataclass(frozen=True)
class Migration:
    """Uma versão de migration: a pasta V<n>__<description>/ com up.sql e down.sql."""

    version: int
    description: str
    up_path: Path
    down_path: Path
    checksum: str


def discover_migrations(migrations_dir: Path) -> list[Migration]:
    """Lê as pastas V<n>__<description>/ e retorna as migrations ordenadas por versão."""
    migrations: dict[int, Migration] = {}

    for entry in migrations_dir.iterdir():
        if entry.name.startswith("."):
            continue

        match = MIGRATION_DIR_PATTERN.match(entry.name)
        if not entry.is_dir() or not match:
            raise MigrationError(
                f"'{entry.name}' fora do padrão: esperado uma pasta V<n>__<description>/"
            )

        version = int(match.group(1))
        if version in migrations:
            raise MigrationError(
                f"Versão {version} duplicada: "
                f"'{migrations[version].up_path.parent.name}' e '{entry.name}'"
            )

        up_path = entry / "up.sql"
        down_path = entry / "down.sql"
        for path in (up_path, down_path):
            if not path.is_file():
                raise MigrationError(f"'{entry.name}' sem o arquivo obrigatório {path.name}")

        migrations[version] = Migration(
            version=version,
            description=match.group(2),
            up_path=up_path,
            down_path=down_path,
            checksum=_checksum(up_path, down_path),
        )

    return [migrations[version] for version in sorted(migrations)]


def _checksum(up_path: Path, down_path: Path) -> str:
    """SHA-256 que muda se o up.sql OU o down.sql for alterado."""
    up_hash = hashlib.sha256(up_path.read_bytes()).hexdigest()
    down_hash = hashlib.sha256(down_path.read_bytes()).hexdigest()
    return hashlib.sha256(f"{up_hash}:{down_hash}".encode()).hexdigest()
