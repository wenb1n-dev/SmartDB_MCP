from databases.base.base import (
    TableName,
    TableDescription,
    DatabaseVersion,
    TableIndex,
    DatabaseHealth,
    SqlOptimize,
)
from databases.database_factory import DatabaseOperationFactory
from databases.mssqlserver.mssqlserver_db_version import MSSQLServerDatabaseVersion
from databases.mssqlserver.mssqlserver_health import MSSQLServerHealth
from databases.mssqlserver.mssqlserver_table_description import MSSQLServerTableDescription
from databases.mssqlserver.mssqlserver_table_index import MSSQLServerTableIndex
from databases.mssqlserver.mssqlserver_optimize import MSSQLServerSqlOptimize


class MSSQLServerFactory(DatabaseOperationFactory):
    name = "mssqlserver"
    def create_table_name(self) -> TableName:
        pass

    def create_table_description(self) -> TableDescription:
        return MSSQLServerTableDescription()

    def create_db_version(self) -> DatabaseVersion:
        return MSSQLServerDatabaseVersion()

    def create_table_index(self) -> TableIndex:
        return MSSQLServerTableIndex()

    def create_db_health(self) -> DatabaseHealth:
        return MSSQLServerHealth()

    def create_sql_optimize(self) -> SqlOptimize:
        return MSSQLServerSqlOptimize()


