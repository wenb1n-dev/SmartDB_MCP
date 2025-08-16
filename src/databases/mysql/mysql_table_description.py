from config.dbconfig import get_db_configs, get_db_config_by_name
from databases.base.base import TableDescription
from utils.execute_sql_util import ExecuteSqlUtil
from databases.mysql.mysql_queries import MySQLQueries


class MySQLTableDescription(TableDescription):

    def get_table_description(self, pool_name: str,database: str, schema: str, table_name: str) -> str:
        db_config = get_db_config_by_name(pool_name)

        if database is None:
            database = db_config.get("database")

        # 将输入的表名按逗号分割成列表
        table_names = [name.strip() for name in table_name.split(',')]
        sql = MySQLQueries.get_table_description(database, table_names)

        sql_result = ExecuteSqlUtil.execute_single_statement(pool_name, sql)

        return ExecuteSqlUtil.format_result(sql_result)
