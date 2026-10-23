"""ES index names listing MCP tool.

Lists indices in an Elasticsearch cluster, optionally filtered by pattern.
"""

from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from datasource.registry import FactoryRegistry
from tools.base import ToolsBase


class GetIndexNamesTool(ToolsBase):
    """Elasticsearch 索引列表查询工具

    列出 Elasticsearch 集群中的索引，支持按名称模式过滤。
    仅适用于搜索引擎范式数据源。
    """

    name = "get_index_names"
    applicable_paradigms = [Paradigm.SEARCH_ENGINE]
    description = (
        "查询 Elasticsearch 集群中的索引列表，支持按名称模式过滤。"
        "List indices in an Elasticsearch cluster, with optional name pattern filter."
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
                        "description": "索引名称过滤模式（通配符，如 'log-*'）/ Index name filter pattern (wildcard)"
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
        """List ES indices.

        Args:
            arguments: Dictionary containing:
                - pattern: Optional index name pattern
                - pool_name: Connection pool name

        Returns:
            Sequence[TextContent]: Index list.
        """
        try:
            if "pool_name" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 pool_name 参数")]

            pattern = arguments.get("pattern")
            pool_name = arguments["pool_name"]

            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            handler = factory.create_index_lister()

            result = handler.get_index_names(pool_name, pattern)

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"查询索引列表时出错: {str(e)}")]
