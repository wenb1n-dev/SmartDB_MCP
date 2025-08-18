from databases.base.base import (
    DatabaseVersion,
    TableDescription,
    TableName,
    TableIndex,
    DatabaseHealth,
    SqlOptimize,
)
from databases.database_factory import DatabaseOperationFactory
from databases.postgresql.postgresql_health import PostgresqlHealth
from databases.postgresql.postgresql_table_index import PostgresqlTableIndex
from databases.postgresql.postgresql_table_name import PostgresqlTableName
from databases.postgresql.postgresql_db_version import PostgresqlDatabaseVersionTool
from databases.postgresql.postgresql_table_description import PostgresqlTableDescription
from databases.postgresql.postgresql_optimize import PostgresqlSqlOptimize


class PostgresqlFactory(DatabaseOperationFactory):

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