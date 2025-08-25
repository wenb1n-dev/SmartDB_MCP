from databases.base.base import SqlOptimize
from databases.mysql.mysql_queries import MySQLQueries
from utils.execute_sql_util import ExecuteSqlUtil


class MySQLSqlOptimize(SqlOptimize):

    def get_sql_explain(self, pool_name: str, text: str):
        sql = "EXPLAIN " + text

        sql_explain = ExecuteSqlUtil.format_result(ExecuteSqlUtil.execute_single_statement(pool_name, sql))

        return sql_explain

    def get_table_size(self, pool_name: str, database: str, schema: str, table_name: str):
        # 将输入的表名按逗号分割成列表
        table_names = [name.strip() for name in table_name.split(',')]

        sql = MySQLQueries.get_table_size(database,table_names)

        return ExecuteSqlUtil.format_result(ExecuteSqlUtil.execute_single_statement(pool_name, sql))

