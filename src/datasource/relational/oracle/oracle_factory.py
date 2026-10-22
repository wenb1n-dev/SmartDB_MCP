from datasource.base import DatabaseVersion, DatabaseHealth
from datasource.relational.base import TableDescription, TableName, TableIndex, SqlOptimize
from datasource.relational.base import RelationalDataSourceFactory
from datasource.relational.oracle.oracle_db_version import OracleDatabaseVersionTool
from datasource.relational.oracle.oracle_health import OracleHealth
from datasource.relational.oracle.oracle_table_description import OracleTableDescription
from datasource.relational.oracle.oracle_table_index import OracleTableIndex
from datasource.relational.oracle.oracle_table_name import OracleTableName
from datasource.relational.oracle.oracle_optimize import OracleSqlOptimize
from permission.base import SqlPermissionPolicy


class OracleFactory(RelationalDataSourceFactory):
    name = "oracle"
    def create_db_version(self) -> DatabaseVersion:
        return OracleDatabaseVersionTool()

    def create_table_description(self) -> TableDescription:
        return OracleTableDescription()

    def create_table_name(self) -> TableName:
        return OracleTableName()

    def create_table_index(self) -> TableIndex:
        return OracleTableIndex()

    def create_db_health(self) -> DatabaseHealth:
        return OracleHealth()

    def create_sql_optimize(self) -> SqlOptimize:
        return OracleSqlOptimize()

    def create_permission_policy(self) -> SqlPermissionPolicy:
        return SqlPermissionPolicy()