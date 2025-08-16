from databases.base.base import DatabaseVersion
from utils.execute_sql_util import ExecuteSqlUtil
from databases.mysql.mysql_queries import MySQLQueries


class MySQLDatabaseVersionTool(DatabaseVersion):

    def get_db_version(self, pool_name: str) -> str:
        sql = MySQLQueries.get_db_version()

        sql_result = ExecuteSqlUtil.execute_single_statement(pool_name, sql)

        return ExecuteSqlUtil.format_result(sql_result)