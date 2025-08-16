from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from databases.database_factory import DatabaseOperationFactory
from tools.base import ToolsBase

class GetTableIndex(ToolsBase):
    name = "get_table_index"
    description = (
        "根据表名搜索数据库中对应的表索引,支持多表查询(Search for table indexes in the database based on table names, supporting multi-table queries)"
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
                        "description": "要搜索表索引情况的表名，支持多个表名，用逗号分隔"
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

                pool_name = arguments.get("pool_name", "default")

                database = arguments.get("database", "default")

                database = database if database != "default" else None

                schema = arguments.get("schema", "default")
                schema = schema if schema != "default" else None

                factory = DatabaseOperationFactory.get_factory_by_pool_name(pool_name)

                handler = factory.create_table_index()

                sql_result = handler.get_table_index(pool_name,database, schema, text)

                return [TextContent(type="text", text=sql_result)]

            except Exception as e:
                return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]