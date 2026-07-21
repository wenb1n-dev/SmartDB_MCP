"""Vector collection info MCP tool.

Queries collection metadata for Milvus vector collections.
"""

from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from databases.database_factory import FactoryRegistry
from tools.base import ToolsBase


class GetCollectionInfoTool(ToolsBase):
    """向量集合信息查询工具

    查询向量集合的元数据：名称、维度、距离度量、Schema、实体数量等。
    仅适用于向量范式数据源。
    """

    name = "get_collection_info"
    applicable_paradigms = [Paradigm.VECTOR]
    description = (
        "查询向量集合的元数据（维度、距离度量、Schema、实体数量等）。"
        "Query vector collection metadata (dimension, metric type, schema, entity count)."
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
                        "description": "集合名称。不指定则查询所有集合的基本信息 / Collection name. If not specified, lists all collections"
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
        """Query collection info.

        Args:
            arguments: Dictionary containing:
                - collection: Collection name (optional)
                - pool_name: Connection pool name (default: "default")

        Returns:
            Sequence[TextContent]: Collection info.
        """
        try:
            if "pool_name" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 pool_name 参数")]

            collection = arguments.get("collection")
            pool_name = arguments["pool_name"]

            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            handler = factory.create_collection_info()

            result = handler.get_collection_info(pool_name, collection)

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"查询集合信息时出错: {str(e)}")]
