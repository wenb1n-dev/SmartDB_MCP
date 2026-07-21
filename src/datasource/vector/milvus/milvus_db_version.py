"""Milvus version query handler."""

from connection.pool_manager import MultiDBPoolManager


class MilvusDatabaseVersion:
    """Query Milvus server version via get_server_version()."""

    def get_db_version(self, pool_name: str) -> str:
        """Get Milvus server version.

        Args:
            pool_name: Connection pool name.

        Returns:
            Milvus version string.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        with pool.connection() as client:
            try:
                version = client.get_server_version()
                return f"Milvus Version: {version}"
            except Exception as e:
                return f"查询 Milvus 版本失败: {str(e)}"
