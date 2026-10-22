from datasource.base import DatabaseVersion, DatabaseHealth
from datasource.relational.base import TableDescription, TableName, TableIndex, SqlOptimize
from datasource.relational.base import RelationalDataSourceFactory
from datasource.relational.mysql.mysql_db_version import MySQLDatabaseVersionTool
from datasource.relational.mysql.mysql_table_description import MySQLTableDescription
from datasource.relational.mysql.mysql_table_index import MySQLTableIndex
from datasource.relational.mysql.mysql_table_name import MySQLTableName
from datasource.relational.mysql.mysql_health import MySQLHealth
from datasource.relational.mysql.mysql_optimize import MySQLSqlOptimize
from permission.base import SqlPermissionPolicy


class MySQLFactory(RelationalDataSourceFactory):

    name: str = "mysql"

    def create_db_version(self) -> DatabaseVersion:
        return MySQLDatabaseVersionTool()

    def create_table_description(self) -> TableDescription:
        return MySQLTableDescription()

    def create_table_name(self) -> TableName:
        return MySQLTableName()

    def create_table_index(self) -> TableIndex:
        return MySQLTableIndex()

    def create_db_health(self) -> DatabaseHealth:
        return MySQLHealth()

    def create_sql_optimize(self) -> SqlOptimize:
        return MySQLSqlOptimize()

    def create_permission_policy(self) -> SqlPermissionPolicy:
        return SqlPermissionPolicy()