from databases.base.base import SqlOptimize
from databases.postgresql.postgresql_queries import PostgresqlQueries
from utils.execute_sql_util import ExecuteSqlUtil


class PostgresqlSqlOptimize(SqlOptimize):
    def get_sql_explain(self, pool_name: str, text: str):
        sql = "EXPLAIN ANALYZE " + text

        sql_explain = ExecuteSqlUtil.format_result(ExecuteSqlUtil.execute_single_statement(pool_name, sql))

        return sql_explain

    def get_table_size(self, pool_name: str, database: str, schema: str, table_name: str):
        # 将输入的表名按逗号分割成列表
        table_names = [name.strip() for name in table_name.split(',')]

        sql = PostgresqlQueries.get_table_size(schema, table_names)

        return ExecuteSqlUtil.format_result(ExecuteSqlUtil.execute_single_statement(pool_name, sql))

