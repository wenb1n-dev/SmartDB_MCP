from databases.base.base import SqlOptimize
from databases.dameng.dameng_queries import DamengQueries

from utils.execute_sql_util import ExecuteSqlUtil


class DamengSqlOptimize(SqlOptimize):
    def get_sql_explain(self, pool_name: str, text: str):
        sql = "EXPLAIN FOR " + text
        sql_explain = ExecuteSqlUtil.execute_single_statement(pool_name, sql)

        return ExecuteSqlUtil.format_result(sql_explain)

    def get_table_size(self, pool_name: str, database: str, schema: str, table_name: str):
        # 将输入的表名按逗号分割成列表
        table_names = [name.strip() for name in table_name.split(',')]

        sql = DamengQueries.get_table_size(schema, table_names)

        sql_result = ExecuteSqlUtil.execute_single_statement(pool_name, sql)

        return ExecuteSqlUtil.format_result(sql_result)