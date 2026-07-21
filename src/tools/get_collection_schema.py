"""Collection schema inference MCP tool.

Infers the schema of a MongoDB collection by sampling documents.
"""

from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from databases.database_factory import FactoryRegistry
from tools.base import ToolsBase


class GetCollectionSchemaTool(ToolsBase):
    """MongoDB 集合 Schema 推断工具

    通过采样文档推断集合的 Schema（字段名、类型、出现频率）。
    仅适用于文档范式数据源。
    """

    name = "get_collection_schema"
    applicable_paradigms = [Paradigm.DOCUMENT]
    description = (
        "推断 MongoDB 集合的 Schema（字段名、类型、出现频率）。"
        "Infer schema of a MongoDB collection (field names, types, presence)."
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
                        "description": "集合名称 / Collection name"
                    },
                    "sample_size": {
                        "type": "integer",
                        "description": "采样文档数量，默认 1000 / Sample size, default: 1000"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "连接池名称，默认为 default / Connection pool name, default: default"
                    }
                },
                "required": ["collection"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Infer collection schema.

        Args:
            arguments: Dictionary containing:
                - collection: Collection name
                - sample_size: Sample size (default: 1000)
                - pool_name: Connection pool name (default: "default")

        Returns:
            Sequence[TextContent]: Schema inference result.
        """
        try:
            if "collection" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 collection 参数")]

            collection = arguments["collection"]
            sample_size = arguments.get("sample_size", 1000)
            pool_name = arguments.get("pool_name", "default")

            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            handler = factory.create_collection_schema()

            result = handler.get_collection_schema(pool_name, collection, sample_size)

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"推断 Schema 时出错: {str(e)}")]
