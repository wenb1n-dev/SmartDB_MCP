from config.dbconfig import get_db_config_by_name
from databases.base.base import TableIndex
from databases.postgresql.postgresql_queries import PostgresqlQueries
from utils.execute_sql_util import ExecuteSqlUtil


class PostgresqlTableIndex(TableIndex):
    def get_table_index(self, pool_name: str, database: str, schema: str, table_name: str) -> str:
        db_config = get_db_config_by_name(pool_name)

        database = db_config.get("database") if database is None else database

        if database != db_config.get("database"):
            raise Exception("PostgreSQL 不支持跨数据库的直接引用")

        if schema is None:
            schema = db_config.get("schema", "public")

        # 将输入的表名按逗号分割成列表
        table_names = [name.strip() for name in table_name.split(',')]

        sql = PostgresqlQueries.get_table_index(schema, table_names)

        sql_result = ExecuteSqlUtil.execute_single_statement(pool_name, sql)

        return ExecuteSqlUtil.format_result(sql_result)

