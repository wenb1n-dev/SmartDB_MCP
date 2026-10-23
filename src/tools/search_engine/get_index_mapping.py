"""ES index mapping MCP tool.

Queries index mappings (field types, analyzers) for Elasticsearch indices.
"""

from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from datasource.registry import FactoryRegistry
from tools.base import ToolsBase


class GetIndexMappingTool(ToolsBase):
    """Elasticsearch 索引 mapping 查询工具

    查询 Elasticsearch 索引的 mapping（字段类型、分析器）和基本设置。
    仅适用于搜索引擎范式数据源。
    """

    name = "get_index_mapping"
    applicable_paradigms = [Paradigm.SEARCH_ENGINE]
    description = (
        "查询 Elasticsearch 索引的 mapping（字段类型、分析器）和设置。"
        "Query Elasticsearch index mappings (field types, analyzers) and settings."
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "index": {
                        "type": "string",
                        "description": "索引名称（可用逗号分隔多个索引）/ Index name (comma-separated for multiple)"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "连接池名称，默认为 default / Connection pool name, default: default"
                    }
                },
                "required": ["index", "pool_name"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Query index mapping.

        Args:
            arguments: Dictionary containing:
                - index: Index name
                - pool_name: Connection pool name

        Returns:
            Sequence[TextContent]: Mapping info.
        """
        try:
            if "index" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 index 参数")]
            if "pool_name" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 pool_name 参数")]

            index = arguments["index"]
            pool_name = arguments["pool_name"]

            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            handler = factory.create_index_mapping()

            result = handler.get_index_mapping(pool_name, index)

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"查询 mapping 时出错: {str(e)}")]
