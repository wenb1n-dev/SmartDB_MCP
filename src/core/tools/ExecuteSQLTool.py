from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from core.exception.exceptions import SQLExecutionError
from core.handles.ToolHandler import ToolHandler


class ExecuteSQLTool(ToolHandler):
    """SQL 执行处理器"""

    name = "execute_sql"
    description = "在MySQL数据库上执行SQL (支持多条SQL语句，以分号分隔)"


    def get_tool_description(self) -> Tool:
        """获取工具描述"""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要执行的SQL语句"
                    },
                    "type": {
                        "type": "string",
                        "description": "数据库名,若没有指定库默认是default"
                    }
                },
                "required": ["query"]
            }
        )


    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """执行SQL工具

                Args:
                    arguments: 包含SQL查询的参数字典

                Returns:
                    执行结果文本序列
                """
        if "query" not in arguments:
            return [TextContent(type="text", text="错误: 缺少查询语句")]

        query = arguments["query"]

        if "type" not in arguments:
            type = "default"
        else:
            type = arguments["type"]

        print(f"正在使用数据库: {type}")

        try:
            from core.handles.DatabaseFactory import DatabaseFactory

            handler = DatabaseFactory.get_db_tool(type)

            sql_results = handler.execute_sql(type,query)


            return [TextContent(type="text", text="\n---\n".join(sql_results))]

        except SQLExecutionError as e:
            return [TextContent(type="text", text=str(e))]


