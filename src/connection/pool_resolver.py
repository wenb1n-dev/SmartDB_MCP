"""连接池名称统一解析入口。

历史上各工具自行执行 ``arguments.get("pool_name", "default")``，默认池是否存在、
显式池是否合法没有统一保证。本模块把「显式池 -> default 池 -> fail-closed」收口，
确保权限校验和后续执行引用同一个明确的 pool_name。
"""

from __future__ import annotations

from typing import Optional

from config.dbconfig import get_db_configs
from core.exceptions import ConfigurationError

DEFAULT_POOL_NAME = "default"


class PoolResolver:
    """连接池名称解析器。"""

    @staticmethod
    def resolve(explicit_pool_name: Optional[str] = None) -> str:
        """解析工具调用应使用的连接池名称。

        Args:
            explicit_pool_name: 调用方显式传入的 pool_name；空字符串等同未传。

        Returns:
            已确认存在于配置和运行时连接池注册表中的池名。

        Raises:
            ConfigurationError: 显式池不存在，或未传池名且 default 池不存在。
        """
        from connection.pool_manager import MultiDBPoolManager

        configs = get_db_configs()
        runtime_pools = MultiDBPoolManager.get_pool_names()

        if explicit_pool_name:
            pool_name = str(explicit_pool_name).strip()
            if pool_name not in configs:
                available = ", ".join(sorted(configs)) or "(空)"
                raise ConfigurationError(
                    f"连接池 '{pool_name}' 不存在，可用连接池: {available}"
                )
            if pool_name not in runtime_pools:
                raise ConfigurationError(
                    f"连接池 '{pool_name}' 未完成初始化，已拒绝执行"
                )
            return pool_name

        if DEFAULT_POOL_NAME not in configs:
            available = ", ".join(sorted(configs)) or "(空)"
            raise ConfigurationError(
                "未传入 pool_name，且配置中不存在必需的 'default' 连接池；"
                f"当前可用连接池: {available}"
            )
        if DEFAULT_POOL_NAME not in runtime_pools:
            raise ConfigurationError(
                "默认连接池 'default' 未完成初始化，已拒绝执行"
            )
        return DEFAULT_POOL_NAME


pool_resolver = PoolResolver()
