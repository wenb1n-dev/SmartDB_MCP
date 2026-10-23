"""Kafka consumer lag MCP tool.

Queries consumer group lag information for a Kafka cluster.
When group_id is specified, returns lag for that group only;
otherwise lists all consumer groups with their lag.
"""

from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from datasource.registry import FactoryRegistry
from tools.base import ToolsBase


class GetConsumerLagTool(ToolsBase):
    """Kafka 消费者延迟查询工具

    查询 Kafka 消费者组的延迟（Lag）信息。指定 group_id 时仅查询该组，
    不指定时列出所有消费者组的延迟。
    仅适用于消息队列范式数据源。
    """

    name = "get_consumer_lag"
    applicable_paradigms = [Paradigm.MESSAGE_QUEUE]
    description = (
        "查询 Kafka 消费者组延迟（Lag）信息。指定 group_id 时仅查询该组，"
        "不指定时列出所有消费者组。"
        "Query Kafka consumer group lag. Specify group_id for a single group, "
        "or list all groups when omitted."
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "group_id": {
                        "type": "string",
                        "description": "消费者组 ID（可选，不指定则列出所有组）/ Consumer group ID (optional, lists all groups if omitted)"
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
        """Get Kafka consumer lag.

        Args:
            arguments: Dictionary containing:
                - group_id: Optional consumer group ID
                - pool_name: Connection pool name

        Returns:
            Sequence[TextContent]: Consumer lag info.
        """
        try:
            if "pool_name" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 pool_name 参数")]

            group_id = arguments.get("group_id")
            pool_name = arguments["pool_name"]

            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            handler = factory.create_consumer_lag()

            result = handler.get_consumer_lag(pool_name, group_id)

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"查询消费者延迟时出错: {str(e)}")]
