from config.dbconfig import get_db_config_by_name
from databases.base.base import TableName
from databases.dameng.dameng_queries import DamengQueries
from utils.execute_sql_util import ExecuteSqlUtil



class DamengTableName(TableName):
    def get_table_name(self, pool_name: str, database: str, schema: str, text: str) -> str:
        db_config = get_db_config_by_name(pool_name)

        if schema is None:
            schema = db_config.get("schema")


        sql = DamengQueries.get_table_names(schema, text)

        sql_result = ExecuteSqlUtil.execute_single_statement(pool_name, sql)

        return ExecuteSqlUtil.format_result(sql_result)
