from databases.base.base import DatabaseVersion
from databases.dameng.dameng_queries import DamengQueries
from utils.execute_sql_util import ExecuteSqlUtil



class DamengDatabaseVersionTool(DatabaseVersion):

    def get_db_version(self, pool_name: str) -> str:
        sql = DamengQueries.get_db_version()

        sql_result = ExecuteSqlUtil.execute_single_statement(pool_name, sql)

        return ExecuteSqlUtil.format_result(sql_result)