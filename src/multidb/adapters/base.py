from abc import ABC, abstractmethod

from multidb.core import Migration


class Adapter(ABC):
    """Contrato que todo adaptador de engine deve cumprir.

    O núcleo só conversa com o banco através destes métodos, sem saber
    qual engine está do outro lado.
    """

    # Se False, uma migration que falhar no meio pode deixar alterações
    # parciais no banco (ex.: MySQL e Databricks fazem commit implícito em DDL).
    transactional_ddl: bool = True

    @abstractmethod
    def connect(self) -> None:
        """Abre a conexão. Deve falhar rápido e com mensagem clara."""

    @abstractmethod
    def close(self) -> None:
        """Fecha a conexão."""

    @abstractmethod
    def ensure_control_table(self) -> None:
        """Cria a tabela de controle de migrations, se ainda não existir."""

    @abstractmethod
    def applied_migrations(self) -> dict[int, str]:
        """Retorna {versão: checksum} de todas as migrations já aplicadas."""

    @abstractmethod
    def apply(self, migration: Migration, applied_by: str) -> None:
        """Executa o up.sql e registra a migration na tabela de controle."""

    @abstractmethod
    def rollback(self, migration: Migration) -> None:
        """Executa o down.sql e remove o registro da tabela de controle."""

    def __enter__(self) -> "Adapter":
        self.connect()
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
