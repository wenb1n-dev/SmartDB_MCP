from datasource.base import DatabaseVersion, DatabaseHealth
from datasource.relational.base import TableDescription, TableName, TableIndex, SqlOptimize
from datasource.relational.base import RelationalDataSourceFactory
from datasource.relational.postgresql.postgresql_health import PostgresqlHealth
from datasource.relational.postgresql.postgresql_table_index import PostgresqlTableIndex
from datasource.relational.postgresql.postgresql_table_name import PostgresqlTableName
from datasource.relational.postgresql.postgresql_db_version import PostgresqlDatabaseVersionTool
from datasource.relational.postgresql.postgresql_table_description import PostgresqlTableDescription
from datasource.relational.postgresql.postgresql_optimize import PostgresqlSqlOptimize
from permission.base import SqlPermissionPolicy


class PostgresqlFactory(RelationalDataSourceFactory):

    name = "postgresql"

    def create_db_version(self) -> DatabaseVersion:
        return PostgresqlDatabaseVersionTool()

    def create_table_description(self) -> TableDescription:
        return PostgresqlTableDescription()

    def create_table_name(self) -> TableName:
        return PostgresqlTableName()

    def create_table_index(self) -> TableIndex:
        return PostgresqlTableIndex()

    def create_db_health(self) -> DatabaseHealth:
        return PostgresqlHealth()

    def create_sql_optimize(self) -> SqlOptimize:
        return PostgresqlSqlOptimize()

    def create_permission_policy(self) -> SqlPermissionPolicy:
        return SqlPermissionPolicy()