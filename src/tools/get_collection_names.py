"""Collection names listing MCP tool.

Lists collections in a MongoDB database, optionally filtered by name pattern.
"""

from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from databases.database_factory import FactoryRegistry
from tools.base import ToolsBase


class GetCollectionNamesTool(ToolsBase):
    """MongoDB 集合列表查询工具

    列出数据库中的所有集合，支持按名称模式过滤。
    仅适用于文档范式数据源。
    """

    name = "get_collection_names"
    applicable_paradigms = [Paradigm.DOCUMENT]
    description = (
        "查询 MongoDB 数据库中的集合列表，支持按名称模式过滤。"
        "List collections in a MongoDB database, with optional name pattern filter."
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "集合名称过滤模式（正则表达式，大小写不敏感）/ Collection name filter pattern (regex, case-insensitive)"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "连接池名称，默认为 default / Connection pool name, default: default"
                    }
                },
                "required": []
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """List collections.

        Args:
            arguments: Dictionary containing:
                - pattern: Optional name pattern filter
                - pool_name: Connection pool name (default: "default")

        Returns:
            Sequence[TextContent]: Collection list.
        """
        try:
            pattern = arguments.get("pattern")
            pool_name = arguments.get("pool_name", "default")

            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            handler = factory.create_collection_names()

            result = handler.get_collection_names(pool_name, pattern)

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"获取集合列表时出错: {str(e)}")]
