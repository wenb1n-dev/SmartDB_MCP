"""Kafka topic info MCP tool.

Queries detailed information for a specific Kafka topic, including
partitions, leaders, end offsets, and configuration.
"""

from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from datasource.registry import FactoryRegistry
from tools.base import ToolsBase


class GetTopicInfoTool(ToolsBase):
    """Kafka topic 详情查询工具

    查询指定 topic 的分区、Leader、末尾 offset 及配置信息。
    仅适用于消息队列范式数据源。
    """

    name = "get_topic_info"
    applicable_paradigms = [Paradigm.MESSAGE_QUEUE]
    description = (
        "查询 Kafka 指定 topic 的详细信息（分区、Leader、end offset、配置）。"
        "Get detailed info for a specific Kafka topic (partitions, leader, end offset, config)."
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "topic_name": {
                        "type": "string",
                        "description": "topic 名称 / Topic name"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "连接池名称，默认为 default / Connection pool name, default: default"
                    }
                },
                "required": ["topic_name", "pool_name"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Get Kafka topic info.

        Args:
            arguments: Dictionary containing:
                - topic_name: Topic name
                - pool_name: Connection pool name

        Returns:
            Sequence[TextContent]: Topic info.
        """
        try:
            if "topic_name" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 topic_name 参数")]
            if "pool_name" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 pool_name 参数")]

            topic_name = arguments["topic_name"]
            pool_name = arguments["pool_name"]

            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            handler = factory.create_topic_info()

            result = handler.get_topic_info(pool_name, topic_name)

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"查询 topic 信息时出错: {str(e)}")]
