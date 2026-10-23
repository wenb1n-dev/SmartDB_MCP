"""Key info query MCP tool.

Queries Redis key metadata: type, size, TTL, memory usage.
"""

from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from datasource.registry import FactoryRegistry
from tools.base import ToolsBase


class GetKeyInfoTool(ToolsBase):
    """Redis Key 信息查询工具

    查询指定 Key 的类型、大小、TTL、内存使用等信息。
    仅适用于 KV 范式数据源。
    """

    name = "get_key_info"
    applicable_paradigms = [Paradigm.KV_STORE]
    description = (
        "查询 Redis Key 的详细信息（类型、大小、TTL、内存使用）。"
        "Query detailed information of a Redis key (type, size, TTL, memory usage)."
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "要查询的 Redis Key 名称"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "连接池名称，默认为 default"
                    }
                },
                "required": ["key"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Query key information.

        Args:
            arguments: Dictionary containing:
                - key: The Redis key to query
                - pool_name: Connection pool name (default: "default")

        Returns:
            Sequence[TextContent]: Key info result.
        """
        try:
            if "key" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 key 参数")]

            key = arguments["key"]
            pool_name = arguments.get("pool_name", "default")

            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            handler = factory.create_key_info()

            result = handler.get_key_info(pool_name, key)

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"查询 Key 信息时出错: {str(e)}")]
