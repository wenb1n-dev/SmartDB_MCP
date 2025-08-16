from config.dbconfig import get_db_config_by_name
from databases.base.base import TableDescription
from databases.mssqlserver.mssqlserver_queries import MSSQLServerQueries
from utils.execute_sql_util import ExecuteSqlUtil


class MSSQLServerTableDescription(TableDescription):
    def get_table_description(self, pool_name: str,database: str, schema: str, table_name: str) -> str:
        db_config = get_db_config_by_name(pool_name)
        if database is None:
            database = db_config.get("database")
        if schema is None:
            schema = db_config.get("schema", "dbo")

        # 将输入的表名按逗号分割成列表
        table_names = [name.strip() for name in table_name.split(',')]

        sql = MSSQLServerQueries.get_table_description(database, schema, table_names)

        sql_result = ExecuteSqlUtil.execute_single_statement(pool_name, sql)

        return ExecuteSqlUtil.format_result(sql_result)