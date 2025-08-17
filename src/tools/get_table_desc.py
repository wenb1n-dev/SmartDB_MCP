from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from databases.database_factory import DatabaseOperationFactory
from tools.base import ToolsBase

class GetTableDesc(ToolsBase):
    name = "get_table_desc"
    description = (
        "数据库表结构查询工具。仅在用户明确要求查看一个或多个具体数据表的详细结构信息（包括列名、列注释等）时使用此工具。"
        "注意：此工具不应用于查询数据库中的所有表名，如需查询所有表名，请使用其他专门工具。"
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "tables": {
                        "type": "string",
                        "description": "要查询结构的具体表名，支持多个表名，用逗号分隔。注意：请确保表名准确无误"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "数据库连接池名称，默认为default"
                    },
                    "database": {
                        "type": "string",
                        "description": "数据库名称,若无指定默认为default"
                    },
                    "schema": {
                        "type": "string",
                        "description": "数据库模式名称,若无指定默认为default"
                    }
                },
                "required": ["tables"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:

            try:
                if "tables" not in arguments:
                    raise ValueError("缺少查询语句")

                text = arguments["tables"]

                pool_name = arguments.get("pool_name","default")

                database = arguments.get("database","default")

                database = database if database != "default" else None

                schema = arguments.get("schema","default")
                schema = schema if schema != "default" else None

                factory = DatabaseOperationFactory.get_factory_by_pool_name(pool_name)

                handler = factory.create_table_description()

                sql_result = handler.get_table_description(pool_name,database,schema,text)

                return [TextContent(type="text", text=sql_result)]

            except Exception as e:
                return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]