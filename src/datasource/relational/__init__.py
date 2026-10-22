"""Relational database factory package.

Imports all relational factory modules. Each factory subclass is
automatically collected into ``FactoryRegistry._pending`` via
``DataSourceFactory.__init_subclass__``. Registration is performed by
``datasource/__init__.py`` via ``FactoryRegistry.register_pending()``
after all paradigm packages are imported.
"""

from datasource.relational.base import (
    RelationalDataSourceFactory,
    TableDescription,
    TableName,
    TableIndex,
    SqlOptimize,
)

# Import factory modules to trigger __init_subclass__ which adds each
# factory to FactoryRegistry._pending.
from datasource.relational.mysql.mysql_factory import MySQLFactory  # noqa: F401
from datasource.relational.postgresql.postgresql_factory import PostgresqlFactory  # noqa: F401
from datasource.relational.oracle.oracle_factory import OracleFactory  # noqa: F401
from datasource.relational.mssqlserver.mssqlserver_factory import MSSQLServerFactory  # noqa: F401
from datasource.relational.dameng.dameng_factory import DamengFactory  # noqa: F401

__all__ = [
    "RelationalDataSourceFactory",
    "TableDescription",
    "TableName",
    "TableIndex",
    "SqlOptimize",
    "MySQLFactory",
    "PostgresqlFactory",
    "OracleFactory",
    "MSSQLServerFactory",
    "DamengFactory",
]
