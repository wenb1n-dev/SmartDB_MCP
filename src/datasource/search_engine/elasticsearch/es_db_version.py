"""Elasticsearch version query handler."""

from connection.pool_manager import MultiDBPoolManager


class ElasticsearchDatabaseVersion:
    """Query Elasticsearch server version via info()."""

    def get_db_version(self, pool_name: str) -> str:
        """Get Elasticsearch server version.

        Args:
            pool_name: Connection pool name.

        Returns:
            ES version string.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        with pool.connection() as client:
            try:
                info = client.info()
                version = info.get("version", {}).get("number", "unknown")
                build_hash = info.get("version", {}).get("build_hash", "unknown")
                cluster_name = info.get("cluster_name", "unknown")
                return f"Elasticsearch Version: {version}, Cluster: {cluster_name}, Build Hash: {build_hash}"
            except Exception as e:
                return f"查询 Elasticsearch 版本失败: {str(e)}"
