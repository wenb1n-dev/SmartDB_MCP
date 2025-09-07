from databases.base.base import (
    DatabaseVersion,
    TableDescription,
    TableName,
    TableIndex,
    DatabaseHealth,
    SqlOptimize,
)
from databases.dameng.dameng_db_version import DamengDatabaseVersionTool
from databases.dameng.dameng_health import DamengHealth
from databases.dameng.dameng_optimize import DamengSqlOptimize
from databases.dameng.dameng_table_description import DamengTableDescription
from databases.dameng.dameng_table_index import DamengTableIndex
from databases.dameng.dameng_table_name import DamengTableName
from databases.database_factory import DatabaseOperationFactory

class DamengFactory(DatabaseOperationFactory):

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