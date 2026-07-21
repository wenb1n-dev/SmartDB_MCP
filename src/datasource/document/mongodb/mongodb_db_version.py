"""MongoDB version query handler."""

from connection.pool_manager import MultiDBPoolManager


class MongoDBDatabaseVersion:
    """Query MongoDB server version via server_info()."""

    def get_db_version(self, pool_name: str) -> str:
        """Get MongoDB server version.

        Args:
            pool_name: Connection pool name.

        Returns:
            MongoDB version string.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        with pool.connection() as client:
            try:
                info = client.server_info()
                version = info.get("version", "unknown")
                git_version = info.get("gitVersion", "unknown")
                return f"MongoDB Version: {version}, Git Version: {git_version}"
            except Exception as e:
                return f"查询 MongoDB 版本失败: {str(e)}"
