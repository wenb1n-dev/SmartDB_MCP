from datasource.base import DatabaseVersion, DatabaseHealth
from datasource.relational.base import TableDescription, TableName, TableIndex, SqlOptimize
from datasource.relational.dameng.dameng_db_version import DamengDatabaseVersionTool
from datasource.relational.dameng.dameng_health import DamengHealth
from datasource.relational.dameng.dameng_optimize import DamengSqlOptimize
from datasource.relational.dameng.dameng_table_description import DamengTableDescription
from datasource.relational.dameng.dameng_table_index import DamengTableIndex
from datasource.relational.dameng.dameng_table_name import DamengTableName
from datasource.relational.base import RelationalDataSourceFactory
from permission.base import SqlPermissionPolicy

class DamengFactory(RelationalDataSourceFactory):

    name: str = "dameng"

    def create_db_version(self) -> DatabaseVersion:
        return DamengDatabaseVersionTool()

    def create_table_description(self) -> TableDescription:
        return DamengTableDescription()

    def create_table_name(self) -> TableName:
        return DamengTableName()

    def create_table_index(self) -> TableIndex:
        return DamengTableIndex()

    def create_db_health(self) -> DatabaseHealth:
        return DamengHealth()

    def create_sql_optimize(self) -> SqlOptimize:
        return DamengSqlOptimize()

    def create_permission_policy(self) -> SqlPermissionPolicy:
        return SqlPermissionPolicy()