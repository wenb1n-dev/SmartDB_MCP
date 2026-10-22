from config.dbconfig import get_db_configs, get_db_config_by_name
from datasource.relational.base import TableDescription
from datasource.relational.dameng.dameng_queries import DamengQueries
from utils.execute_sql_util import ExecuteSqlUtil



class DamengTableDescription(TableDescription):

    def get_table_description(self, pool_name: str,database: str, schema: str, table_name: str) -> str:
        db_config = get_db_config_by_name(pool_name)

        if schema is None:
            schema = db_config.get("schema")

        # 将输入的表名按逗号分割成列表
        table_names = [name.strip() for name in table_name.split(',')]
        sql, params = DamengQueries.get_table_description(schema, table_names)

        sql_result = ExecuteSqlUtil.execute_single_statement(pool_name, sql, params)

        return ExecuteSqlUtil.format_result(sql_result)
