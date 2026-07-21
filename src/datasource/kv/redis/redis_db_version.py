"""Redis version query handler."""

from connection.pool_manager import MultiDBPoolManager


class RedisDatabaseVersion:
    """Query Redis server version via INFO command."""

    def get_db_version(self, pool_name: str) -> str:
        """Get Redis server version.

        Args:
            pool_name: Connection pool name.

        Returns:
            Redis version string.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        with pool.connection() as client:
            info = client.info("server")
            version = info.get("redis_version", "unknown")
            mode = info.get("redis_mode", "standalone")
            os_info = info.get("os", "unknown")
            return f"Redis Version: {version}, Mode: {mode}, OS: {os_info}"
