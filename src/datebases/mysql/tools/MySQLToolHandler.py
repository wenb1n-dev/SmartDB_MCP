from core.tools.ToolsBase import ToolsBase
from datebases.mysql.tools.MySQLExecuteSQLTool import MySQLExecuteSQLTool
from datebases.mysql.tools.MySQLHealthCheckTool import MySQLHealthCheckTool


class MySQLToolHandler(ToolsBase):

    def execute_sql(self, db_name: str, query: str) -> list:
        MySQLExecuteSQLTool.execute_sql(db_name, query)

    def health_check(self, db_name: str) ->  list:
        MySQLHealthCheckTool.health_check(db_name)