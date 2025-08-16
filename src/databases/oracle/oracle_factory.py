from databases.base.base import DatabaseVersion, TableDescription, TableName, TableIndex, DatabaseHealth
from databases.database_factory import DatabaseOperationFactory
from databases.oracle.oracle_db_version import OracleDatabaseVersionTool
from databases.oracle.oracle_health import OracleHealth
from databases.oracle.oracle_table_description import OracleTableDescription
from databases.oracle.oracle_table_index import OracleTableIndex
from databases.oracle.oracle_table_name import OracleTableName


class OracleFactory(DatabaseOperationFactory):
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