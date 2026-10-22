"""Redis command execution handler.

Executes Redis commands with permission checking. The command and args
are passed to the Redis client's ``execute_command`` method.
"""

import json
from typing import Any, List, Optional

from connection.pool_manager import MultiDBPoolManager
from permission.redis_permission import RedisPermissionPolicy


class RedisCommandExecutor:
    """Execute Redis commands with permission enforcement."""

    def __init__(self):
        self._policy = RedisPermissionPolicy()

    def execute_command(
        self,
        pool_name: str,
        command: str,
        args: Optional[List[Any]] = None,
    ) -> str:
        """Execute a Redis command.

        Args:
            pool_name: Connection pool name.
            command: Redis command (e.g., GET, SET, HGET, LPUSH).
            args: Command arguments.

        Returns:
            JSON-formatted result string.
        """
        args = args or []
        command_upper = command.upper()

        # Permission check
        self._policy.check_permissions(pool_name, command_upper)

        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        with pool.connection() as client:
            try:
                result = client.execute_command(command_upper, *args)
                return self._format_result(command_upper, result)
            except Exception as e:
                return f"命令执行失败: {str(e)}"

    def _format_result(self, command: str, result: Any) -> str:
        """Format Redis command result to a readable string.

        Args:
            command: The Redis command that was executed.
            result: The raw result from Redis.

        Returns:
            Formatted result string.
        """
        if result is None:
            return f"{command} -> (nil)"

        if isinstance(result, (list, tuple)):
            if not result:
                return f"{command} -> (empty list)"
            lines = [f"{command} -> (list, {len(result)} items)"]
            for i, item in enumerate(result):
                if isinstance(item, bytes):
                    item = item.decode("utf-8", errors="replace")
                lines.append(f"  {i}: {item}")
            return "\n".join(lines)

        if isinstance(result, dict):
            if not result:
                return f"{command} -> (empty dict)"
            lines = [f"{command} -> (dict, {len(result)} fields)"]
            for k, v in result.items():
                if isinstance(k, bytes):
                    k = k.decode("utf-8", errors="replace")
                if isinstance(v, bytes):
                    v = v.decode("utf-8", errors="replace")
                lines.append(f"  {k}: {v}")
            return "\n".join(lines)

        if isinstance(result, bytes):
            return f"{command} -> {result.decode('utf-8', errors='replace')}"

        if isinstance(result, bool):
            return f"{command} -> {'1 (true)' if result else '(nil)'}"

        if isinstance(result, int):
            return f"{command} -> (integer) {result}"

        return f"{command} -> {result}"
