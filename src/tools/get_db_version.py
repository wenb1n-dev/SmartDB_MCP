from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from core.exceptions import SQLExecutionError
from databases.database_factory import DatabaseOperationFactory
from tools.base import ToolsBase


class DatabaseVersion(ToolsBase):
    """SQL 执行处理器"""

    name = "get_db_version"
    description = "查询某个连接池连接的数据库版本号"


    def get_tool_description(self) -> Tool:
        """获取工具描述"""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "pool_name": {
                        "type": "string",
                        "description": "线程池名称,若没有指定默认是default"
                    }
                },
                "required": ["pool_name"]
            }
        )


    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """执行SQL工具

                Args:
                    arguments: 包含SQL查询的参数字典

                Returns:
                    执行结果文本序列
                """
        if "pool_name" not in arguments:
            return [TextContent(type="text", text="错误: 缺少线程池名称")]

        pool_name = arguments["pool_name"]

        try:

            factory = DatabaseOperationFactory.get_factory_by_pool_name(pool_name)

            handler = factory.create_db_version()

            sql_results = handler.get_db_version(pool_name)

            return [TextContent(type="text", text="".join(sql_results))]

        except SQLExecutionError as e:
            return [TextContent(type="text", text=str(e))]


