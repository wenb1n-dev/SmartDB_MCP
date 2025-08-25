from databases.base.base import SqlOptimize


class MSSQLServerSqlOptimize(SqlOptimize):
    def get_sql_explain(self, pool_name: str, sql: str):
        pass

    def get_table_size(self, pool_name: str, database: str, schema: str, table_name: str):
        pass