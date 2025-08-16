from databases.base.base import DatabaseVersion, TableDescription, TableName, TableIndex, DatabaseHealth
from databases.database_factory import DatabaseOperationFactory
from databases.mysql.mysql_db_version import MySQLDatabaseVersionTool

from databases.mysql.mysql_table_description import MySQLTableDescription
from databases.mysql.mysql_table_index import MySQLTableIndex
from databases.mysql.mysql_table_name import MySQLTableName
from databases.mysql.mysql_health import MySQLHealth


class MySQLFactory(DatabaseOperationFactory):

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