"""Key scanning MCP tool.

Scans Redis keys by pattern using the SCAN command.
"""

from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from databases.database_factory import FactoryRegistry
from tools.base import ToolsBase


class ScanKeysTool(ToolsBase):
    """Redis Key 扫描工具

    按 pattern 扫描 Redis Key（使用 SCAN 命令，非阻塞）。
    仅适用于 KV 范式数据源。
    """

    name = "scan_keys"
    applicable_paradigms = [Paradigm.KV_STORE]
    description = (
        "按 pattern 扫描 Redis Key（使用 SCAN 命令，非阻塞）。"
        "Scan Redis keys by pattern using SCAN command (non-blocking)."
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
                        "description": "Key 匹配模式，如 'user:*'、'session:*'。默认为 '*'（匹配所有 Key）"
                    },
                    "count": {
                        "type": "integer",
                        "description": "每次 SCAN 迭代的建议数量，默认为 100"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "连接池名称，默认为 default"
                    }
                },
                "required": []
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Scan keys by pattern.

        Args:
            arguments: Dictionary containing:
                - pattern: Key pattern (default: "*")
                - count: SCAN count hint (default: 100)
                - pool_name: Connection pool name (default: "default")

        Returns:
            Sequence[TextContent]: Scanned key list.
        """
        try:
            pattern = arguments.get("pattern", "*")
            count = arguments.get("count", 100)
            pool_name = arguments.get("pool_name", "default")

            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            handler = factory.create_key_scanner()

            result = handler.scan_keys(pool_name, pattern, count)

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"扫描 Key 时出错: {str(e)}")]
