from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from core.exceptions import SQLExecutionError
from tools.base import ToolsBase
from utils.execute_sql_util import ExecuteSqlUtil


class ExecuteSQLTool(ToolsBase):
    """SQL 执行处理器"""

    name = "execute_sql"
    description = ("该工具仅用于执行由 sql_creator 生成的 SQL。禁止在此工具中直接输入模型自行构造或推测的 SQL 语句。"
                   "通常在 sql_creator 成功生成 SQL 后，才应调用此工具进行执行。"
        "SQL 执行工具，用于在数据库上执行已生成的 SQL 语句（支持多条，以分号分隔）。"
                   )


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
                    "pool_name": {
                        "type": "string",
                        "description": "线程池名称,若没有指定默认是default"
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

        if "pool_name" not in arguments:
            pool_name = "default"
        else:
            pool_name = arguments["pool_name"]

        try:

            sql_results = ExecuteSqlUtil.execute_multiple_statements(pool_name, query)

            results = []
            for result in sql_results:
                formatted_result = ExecuteSqlUtil.format_result(result)
                results.append(formatted_result)

            return [TextContent(type="text", text="\n---\n".join(results))]

        except SQLExecutionError as e:
            return [TextContent(type="text", text=str(e))]


