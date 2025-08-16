from config.dbconfig import get_db_config_by_name
from databases.base.base import TableName
from databases.mssqlserver.mssqlserver_queries import MSSQLServerQueries
from utils.execute_sql_util import ExecuteSqlUtil


class MSSQLServerTableName(TableName):
    def get_table_name(self, pool_name: str, database: str, schema: str, text: str) -> str:
        db_config = get_db_config_by_name(pool_name)

        if database is None:
            database = db_config.get("database")
        if schema is None:
            schema = db_config.get("schema", "dbo")


        sql = MSSQLServerQueries.get_table_names(database, schema, text)

        sql_result = ExecuteSqlUtil.execute_single_statement(pool_name, sql)

        return ExecuteSqlUtil.format_result(sql_result)