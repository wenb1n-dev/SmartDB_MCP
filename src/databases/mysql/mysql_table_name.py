from config.dbconfig import get_db_config_by_name
from databases.base.base import TableName
from utils.execute_sql_util import ExecuteSqlUtil
from databases.mysql.mysql_queries import MySQLQueries


class MySQLTableName(TableName):
    def get_table_name(self, pool_name: str, database: str, schema: str, text: str) -> str:
        db_config = get_db_config_by_name(pool_name)

        if database is None:
            database = db_config.get("database")

        sql = MySQLQueries.get_table_names(database, text)

        sql_result = ExecuteSqlUtil.execute_single_statement(pool_name, sql)

        return ExecuteSqlUtil.format_result(sql_result)
