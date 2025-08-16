from databases.base.base import DatabaseVersion
from databases.oracle.oracle_queries import OracleQueries
from utils.execute_sql_util import ExecuteSqlUtil


class OracleDatabaseVersionTool(DatabaseVersion):
    def get_db_version(self, pool_name: str) -> str:

        sql_result = ExecuteSqlUtil.execute_single_statement(pool_name, OracleQueries.get_db_version())

        return ExecuteSqlUtil.format_result(sql_result)