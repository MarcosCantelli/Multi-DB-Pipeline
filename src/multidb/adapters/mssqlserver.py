import os
import re

import mssql_python

from multidb.adapters.base import Adapter
from multidb.core import Migration

# Linha contendo apenas GO (maiúsculo ou minúsculo), com espaços opcionais.
GO_PATTERN = re.compile(r"^\s*GO\s*$", re.IGNORECASE | re.MULTILINE)

CONTROL_TABLE_DDL = """
IF OBJECT_ID(N'dbo.schema_migrations', N'U') IS NULL
CREATE TABLE dbo.schema_migrations (
    version     INT           NOT NULL PRIMARY KEY,
    description NVARCHAR(200) NOT NULL,
    checksum    CHAR(64)      NOT NULL,
    applied_by  NVARCHAR(200) NOT NULL,
    applied_at  DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME()
);
"""


def split_batches(sql: str) -> list[str]:
    """Divide o script nos separadores GO, como fazem o SSMS e o sqlcmd.

    GO não é T-SQL: o servidor não o reconhece, então quem divide é o cliente.
    """
    batches = GO_PATTERN.split(sql)
    return [batch.strip() for batch in batches if batch.strip()]


def escape_value(value: str) -> str:
    """Protege um valor da connection string ODBC (ex.: senha com ';').

    O valor vai entre chaves e cada '}' interno é duplicado.
    """
    return "{" + value.replace("}", "}}") + "}"


class MssqlServerAdapter(Adapter):
    transactional_ddl = True

    def __init__(self, host: str, port: int, database: str, user: str, password: str) -> None:
        self.connection_string = (
            f"SERVER={escape_value(f'{host},{port}')};"
            f"DATABASE={escape_value(database)};"
            f"UID={escape_value(user)};"
            f"PWD={escape_value(password)};"
            # Lab: certificado autoassinado. Em PRD usar certificado válido
            # e TrustServerCertificate=no.
            "Encrypt=yes;TrustServerCertificate=yes;"
        )
        self.connection = None

    @classmethod
    def from_env(cls) -> "MssqlServerAdapter":
        """Cria o adaptador a partir das variáveis MSSQL_* (preenchidas pela esteira)."""
        return cls(
            host=os.environ["MSSQL_HOST"],
            port=int(os.environ.get("MSSQL_PORT", "1433")),
            database=os.environ["MSSQL_DATABASE"],
            user=os.environ["MSSQL_USER"],
            password=os.environ["MSSQL_PASSWORD"],
        )

    def connect(self) -> None:
        self.connection = mssql_python.connect(
            self.connection_string, autocommit=False, timeout=10
        )

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def ensure_control_table(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(CONTROL_TABLE_DDL)
        self.connection.commit()

    def applied_migrations(self) -> dict[int, str]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT version, checksum FROM dbo.schema_migrations")
        return {version: checksum for version, checksum in cursor.fetchall()}

    def apply(self, migration: Migration, applied_by: str) -> None:
        self._run_in_transaction(
            migration.up_path.read_text(encoding="utf-8"),
            "INSERT INTO dbo.schema_migrations (version, description, checksum, applied_by) "
            "VALUES (%(version)s, %(description)s, %(checksum)s, %(applied_by)s)",
            {
                "version": migration.version,
                "description": migration.description,
                "checksum": migration.checksum,
                "applied_by": applied_by,
            },
        )

    def rollback(self, migration: Migration) -> None:
        self._run_in_transaction(
            migration.down_path.read_text(encoding="utf-8"),
            "DELETE FROM dbo.schema_migrations WHERE version = %(version)s",
            {"version": migration.version},
        )

    def _run_in_transaction(self, script: str, control_sql: str, params: dict) -> None:
        """Executa os lotes do script e o registro de controle numa única transação."""
        cursor = self.connection.cursor()
        try:
            for batch in split_batches(script):
                cursor.execute(batch)
            cursor.execute(control_sql, params)
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
