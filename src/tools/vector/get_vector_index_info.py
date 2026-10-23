"""Vector index info MCP tool.

Queries index information for Milvus vector collections.
"""

from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from datasource.registry import FactoryRegistry
from tools.base import ToolsBase


class GetVectorIndexInfoTool(ToolsBase):
    """向量索引信息查询工具

    查询向量集合的索引信息：索引类型（HNSW/IVF/DISKANN）、参数、构建进度等。
    仅适用于向量范式数据源。
    """

    name = "get_vector_index_info"
    applicable_paradigms = [Paradigm.VECTOR]
    description = (
        "查询向量集合的索引信息（索引类型、参数、构建进度等）。"
        "Query vector index information (index type, parameters, build progress)."
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
        """Query vector index info.

        Args:
            arguments: Dictionary containing:
                - collection: Collection name (optional)
                - pool_name: Connection pool name (default: "default")

        Returns:
            Sequence[TextContent]: Index info.
        """
        try:
            if "pool_name" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 pool_name 参数")]

            collection = arguments.get("collection")
            pool_name = arguments["pool_name"]

            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            handler = factory.create_index_info()

            result = handler.get_index_info(pool_name, collection)

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"查询索引信息时出错: {str(e)}")]
