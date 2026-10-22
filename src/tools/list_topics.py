"""Kafka topic listing MCP tool.

Lists topics in a Kafka cluster, optionally filtered by pattern.
"""

from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from datasource.registry import FactoryRegistry
from tools.base import ToolsBase


class ListTopicsTool(ToolsBase):
    """Kafka topic 列表查询工具

    列出 Kafka 集群中的 topic，支持按名称模式过滤。
    仅适用于消息队列范式数据源。
    """

    name = "list_topics"
    applicable_paradigms = [Paradigm.MESSAGE_QUEUE]
    description = (
        "查询 Kafka 集群中的 topic 列表，支持按名称模式过滤。"
        "List topics in a Kafka cluster, with optional name pattern filter."
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
                        "description": "topic 名称过滤模式（通配符，如 'log-*'）/ Topic name filter pattern (wildcard)"
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
        """List Kafka topics.

        Args:
            arguments: Dictionary containing:
                - pattern: Optional topic name pattern
                - pool_name: Connection pool name

        Returns:
            Sequence[TextContent]: Topic list.
        """
        try:
            if "pool_name" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 pool_name 参数")]

            pattern = arguments.get("pattern")
            pool_name = arguments["pool_name"]

            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            handler = factory.create_topic_lister()

            result = handler.get_topic_names(pool_name, pattern)

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"查询 topic 列表时出错: {str(e)}")]
