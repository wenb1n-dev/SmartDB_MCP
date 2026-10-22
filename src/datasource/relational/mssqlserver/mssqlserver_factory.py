from datasource.base import DatabaseVersion, DatabaseHealth
from datasource.relational.base import TableName, TableDescription, TableIndex, SqlOptimize
from datasource.relational.base import RelationalDataSourceFactory
from datasource.relational.mssqlserver.mssqlserver_db_version import MSSQLServerDatabaseVersion
from datasource.relational.mssqlserver.mssqlserver_health import MSSQLServerHealth
from datasource.relational.mssqlserver.mssqlserver_table_description import MSSQLServerTableDescription
from datasource.relational.mssqlserver.mssqlserver_table_index import MSSQLServerTableIndex
from datasource.relational.mssqlserver.mssqlserver_optimize import MSSQLServerSqlOptimize
from datasource.relational.mssqlserver.mssqlserver_table_name import MSSQLServerTableName
from permission.base import SqlPermissionPolicy


class MSSQLServerFactory(RelationalDataSourceFactory):
    name = "mssqlserver"
    def create_table_name(self) -> TableName:
        return MSSQLServerTableName()

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

    def create_permission_policy(self) -> SqlPermissionPolicy:
        return SqlPermissionPolicy()


