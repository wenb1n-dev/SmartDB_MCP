from databases.base.base import DatabaseVersion
from databases.postgresql.postgresql_queries import PostgresqlQueries
from utils.execute_sql_util import ExecuteSqlUtil


class PostgresqlDatabaseVersionTool(DatabaseVersion):

    def get_db_version(self, pool_name: str) -> str:

        sql = PostgresqlQueries.get_db_version()

        sql_result = ExecuteSqlUtil.execute_single_statement(pool_name, sql)

        return ExecuteSqlUtil.format_result(sql_result)
