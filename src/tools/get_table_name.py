from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from databases.database_factory import DatabaseOperationFactory
from tools.base import ToolsBase

class GetTableName(ToolsBase):
    name = "get_table_name"
    description = (
        "数据库表名查询工具。用于查询数据库中的所有表名或将根据表的中文名称或表描述搜索数据库中对应的表名。"
        "当用户需要列出数据库中的所有表或者根据表的中文描述查找具体表名时使用此工具。"
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要搜索的表描述，搜索包含某个关键词的表名。若要查询所有表，请使用'SEARCH_ALL_TABLES'关键词"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "线程池名称,若没有指定默认是default"
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
                "required": ["text"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:

            try:
                if "text" not in arguments:
                    raise ValueError("缺少查询语句")

                text = arguments["text"]

                pool_name = arguments.get("pool_name", "default")

                database = arguments.get("database", "default")

                database = database if database != "default" else None

                schema = arguments.get("schema", "default")
                schema = schema if schema != "default" else None

                factory = DatabaseOperationFactory.get_factory_by_pool_name(pool_name)

                handler = factory.create_table_name()

                sql_result = handler.get_table_name(pool_name,database, schema, text)

                return [TextContent(type="text", text=sql_result)]

            except Exception as e:
                return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]