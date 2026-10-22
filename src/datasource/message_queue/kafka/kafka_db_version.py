"""Kafka version/broker info handler."""

from connection.pool_manager import MultiDBPoolManager


class KafkaDatabaseVersion:
    """Query Kafka broker version and cluster info."""

    def get_db_version(self, pool_name: str) -> str:
        """Get Kafka broker version and cluster info.

        kafka-python 没有直接返回 broker 软件版本的 API，这里通过
        ``describe_cluster()`` 获取集群 ID、broker 列表与 controller，
        并通过客户端协商得到的 API 版本辅助判断 broker 能力。

        Args:
            pool_name: Connection pool name.

        Returns:
            Kafka cluster/version description string.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        with pool.connection() as admin:
            try:
                # 集群元数据：brokers / controller_id / cluster_id
                cluster = admin.describe_cluster()
                brokers = cluster.get("brokers", [])
                controller_id = cluster.get("controller_id")
                cluster_id = cluster.get("cluster_id", "unknown")

                broker_info = [
                    f"{b.get('host')}:{b.get('port')} (id={b.get('node_id')})"
                    for b in brokers
                ]

                # 客户端与 broker 协商出的 API 版本，形如 (3, 7, 0)，
                # 可近似反映 broker 支持的 Kafka 协议代际。
                api_version = "unknown"
                config_api_version = getattr(admin.config, "get", None)
                if config_api_version is not None:
                    api_version = admin.config.get("api_version", "unknown")

                return (
                    f"Kafka API Version: {api_version}, "
                    f"Cluster ID: {cluster_id}, "
                    f"Controller Broker ID: {controller_id}, "
                    f"Brokers: {len(brokers)} ({', '.join(broker_info)})"
                )
            except Exception as e:
                return f"查询 Kafka 版本失败: {str(e)}"
