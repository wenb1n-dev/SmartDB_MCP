"""Redis command execution MCP tool.

Allows MCP clients to execute Redis commands (GET, SET, HGET, LPUSH, etc.)
with permission enforcement.
"""

import json
from typing import Dict, Sequence, Any, List

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from datasource.registry import FactoryRegistry
from tools.base import ToolsBase


class ExecuteCommandTool(ToolsBase):
    """Redis 命令执行工具

    执行 Redis 命令（GET/SET/HGET/LPUSH 等），带权限校验。
    仅适用于 KV 范式数据源。
    """

    name = "execute_command"
    applicable_paradigms = [Paradigm.KV_STORE]
    description = (
        "执行 Redis 命令（GET/SET/HGET/LPUSH 等），支持所有 Redis 命令。"
        "Execute Redis commands (GET/SET/HGET/LPUSH etc.), supports all Redis commands."
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Redis 命令名称，如 GET、SET、HGET、LPUSH 等"
                    },
                    "args": {
                        "type": "array",
                        "items": {},
                        "description": "命令参数列表。例如 GET 命令的 args 为 ['key']，SET 命令的 args 为 ['key', 'value']"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "连接池名称，默认为 default"
                    }
                },
                "required": ["command"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute a Redis command.

        Args:
            arguments: Dictionary containing:
                - command: Redis command name (e.g., GET, SET)
                - args: Command arguments list
                - pool_name: Connection pool name (default: "default")

        Returns:
            Sequence[TextContent]: Command result.
        """
        try:
            if "command" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 command 参数")]

            command = arguments["command"]
            args = arguments.get("args", [])
            pool_name = arguments.get("pool_name", "default")

            # Get factory and create command executor
            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            executor = factory.create_command_executor()

            # Execute command
            result = executor.execute_command(pool_name, command, args)

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"执行命令时出错: {str(e)}")]
