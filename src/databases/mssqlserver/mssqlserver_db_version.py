from databases.base.base import DatabaseVersion
from databases.mssqlserver.mssqlserver_queries import MSSQLServerQueries
from utils.execute_sql_util import ExecuteSqlUtil


class MSSQLServerDatabaseVersion(DatabaseVersion):
    def get_db_version(self, pool_name: str) -> str:
        sql = MSSQLServerQueries.get_db_version()

        sql_result = ExecuteSqlUtil.execute_single_statement(pool_name, sql)

        return ExecuteSqlUtil.format_result(sql_result)