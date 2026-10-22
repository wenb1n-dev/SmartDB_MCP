"""Relational database abstraction layer.

Defines relational-specific abstract base classes (TableDescription,
TableName, TableIndex, SqlOptimize) and the RelationalDataSourceFactory
that all relational database factories inherit from.

Common ABCs (DatabaseVersion, DatabaseHealth) live in ``datasource.base``
because they apply to all paradigms.

Factory registration is handled uniformly by ``DataSourceFactory.__init_subclass__``
which adds each concrete factory to ``FactoryRegistry._pending``.
``datasource/__init__.py`` calls ``FactoryRegistry.register_pending()``
after all paradigm packages are imported.
"""

from abc import ABC, abstractmethod
from typing import ClassVar

from datasource.base import DataSourceFactory, DatabaseVersion, DatabaseHealth, Paradigm
from datasource.registry import FactoryRegistry


class TableDescription(ABC):
    """Table description interface (relational only)."""

    @abstractmethod
    def get_table_description(self, pool_name: str, database: str, schema: str, table_name: str) -> str:
        """Get table description.

        Args:
            pool_name: Connection pool name.
            database: Database name.
            schema: Schema name.
            table_name: Table name.

        Returns:
            Table description text.
        """
        pass


class TableName(ABC):
    """Table name lookup interface (relational only)."""

    @abstractmethod
    def get_table_name(self, pool_name: str, database: str, schema: str, text: str) -> str:
        """Get table name by keyword.

        Args:
            pool_name: Connection pool name.
            database: Database name.
            schema: Schema name.
            text: Search keyword.

        Returns:
            Matching table names.
        """
        pass


class TableIndex(ABC):
    """Table index interface (relational only)."""

    @abstractmethod
    def get_table_index(self, pool_name: str, database: str, schema: str, table_name: str) -> str:
        """Get table index info.

        Args:
            pool_name: Connection pool name.
            database: Database name.
            schema: Schema name.
            table_name: Table name.
        """
        pass


class SqlOptimize(ABC):
    """SQL optimization interface (relational only)."""

    @abstractmethod
    def get_sql_explain(self, pool_name: str, sql: str):
        """Get SQL execution plan.

        Args:
            pool_name: Connection pool name.
            sql: SQL statement.
        """

    @abstractmethod
    def get_table_size(self, pool_name: str, database: str, schema: str, table_name: str):
        """Get table size.

        Args:
            pool_name: Connection pool name.
            database: Database name.
            schema: Schema name.
            table_name: Table name.
        """


class RelationalDataSourceFactory(DataSourceFactory):
    """Relational database operation factory.

    Inherits common methods (create_db_version, create_db_health) from
    DataSourceFactory and adds relational-specific abstract methods for
    table operations and SQL optimization.

    Factory registration is inherited from ``DataSourceFactory.__init_subclass__``
    which adds each concrete subclass to ``FactoryRegistry._pending``.
    """

    paradigm: ClassVar[Paradigm] = Paradigm.RELATIONAL

    @abstractmethod
    def create_db_version(self) -> DatabaseVersion:
        pass

    @abstractmethod
    def create_table_description(self) -> TableDescription:
        pass

    @abstractmethod
    def create_table_name(self) -> TableName:
        pass

    @abstractmethod
    def create_table_index(self) -> TableIndex:
        pass

    @abstractmethod
    def create_db_health(self) -> DatabaseHealth:
        pass

    @abstractmethod
    def create_sql_optimize(self) -> SqlOptimize:
        pass
