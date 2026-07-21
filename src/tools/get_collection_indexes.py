"""Collection indexes query MCP tool.

Lists indexes on MongoDB collections.
"""

from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from databases.database_factory import FactoryRegistry
from tools.base import ToolsBase


class GetCollectionIndexesTool(ToolsBase):
    """MongoDB 集合索引查询工具

    查询指定集合或所有集合的索引信息。
    仅适用于文档范式数据源。
    """

    name = "get_collection_indexes"
    applicable_paradigms = [Paradigm.DOCUMENT]
    description = (
        "查询 MongoDB 集合的索引信息，支持查询单个集合或所有集合。"
        "Query index information for a MongoDB collection or all collections."
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "description": "集合名称。不指定则查询所有集合的索引 / Collection name. If not specified, lists indexes for all collections"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "连接池名称，默认为 default / Connection pool name, default: default"
                    }
                },
                "required": ["pool_name"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Query collection indexes.

        Args:
            arguments: Dictionary containing:
                - collection: Collection name (optional, lists all if not specified)
                - pool_name: Connection pool name (default: "default")

        Returns:
            Sequence[TextContent]: Index information.
        """
        try:
            if "pool_name" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 pool_name 参数")]

            collection = arguments.get("collection")
            pool_name = arguments["pool_name"]

            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            handler = factory.create_collection_indexes()

            result = handler.get_collection_indexes(pool_name, collection)

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"查询索引信息时出错: {str(e)}")]
