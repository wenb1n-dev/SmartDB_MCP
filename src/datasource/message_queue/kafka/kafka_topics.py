"""Kafka topic listing handler.

Lists topics in a Kafka cluster, optionally filtered by pattern.
"""

import json
from typing import Optional

from connection.pool_manager import MultiDBPoolManager
from datasource.base import Paradigm
from permission.enforcer import enforcer


class KafkaTopics:
    """List and query topics in a Kafka cluster."""

    def get_topic_names(
        self,
        pool_name: str,
        pattern: Optional[str] = None,
    ) -> str:
        """List topics in the cluster.

        Args:
            pool_name: Connection pool name.
            pattern: Optional topic name pattern (simple wildcard match).

        Returns:
            JSON-formatted topic list.
        """
        # 统一鉴权入口：Topic 列表读取按目标执行池鉴权
        enforcer.authorize_category(
            pool_name,
            "LIST_TOPICS",
            Paradigm.MESSAGE_QUEUE,
            tool="list_topics",
        ).raise_if_denied()

        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        try:
            from kafka import KafkaConsumer
            consumer = KafkaConsumer(
                bootstrap_servers=pool.bootstrap_servers,
                request_timeout_ms=10000,
                api_version_auto_timeout_ms=5000,
            )
            try:
                topics = sorted(consumer.topics())

                if not topics:
                    return json.dumps(
                        {"total_topics": 0, "topics": [], "message": "集群中没有 topic"},
                        ensure_ascii=False, indent=2,
                    )

                # Filter by pattern
                if pattern:
                    import fnmatch
                    topics = [t for t in topics if fnmatch.fnmatch(t, pattern)]

                result = {
                    "total_topics": len(topics),
                    "topics": [],
                }

                for topic in topics:
                    partitions = consumer.partitions_for_topic(topic)
                    partition_count = len(partitions) if partitions else 0
                    result["topics"].append({
                        "name": topic,
                        "partition_count": partition_count,
                    })

                return json.dumps(result, ensure_ascii=False, indent=2, default=str)
            finally:
                consumer.close(autocommit=False)

        except Exception as e:
            return f"获取 topic 列表失败: {str(e)}"

    def get_topic_info(
        self,
        pool_name: str,
        topic_name: str,
    ) -> str:
        """Get detailed info for a specific topic.

        Args:
            pool_name: Connection pool name.
            topic_name: Topic name to query.

        Returns:
            JSON-formatted topic info including partitions, leaders, and ISR.
        """
        # 统一鉴权入口：Topic 元数据读取按目标执行池鉴权
        enforcer.authorize_category(
            pool_name,
            "DESCRIBE_TOPIC",
            Paradigm.MESSAGE_QUEUE,
            tool="get_topic_info",
        ).raise_if_denied()

        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        try:
            from kafka import KafkaConsumer
            from kafka import TopicPartition

            consumer = KafkaConsumer(
                bootstrap_servers=pool.bootstrap_servers,
                request_timeout_ms=10000,
                api_version_auto_timeout_ms=5000,
            )
            try:
                partitions = consumer.partitions_for_topic(topic_name)
                if not partitions:
                    return json.dumps(
                        {"topic": topic_name, "error": "topic 不存在或没有分区"},
                        ensure_ascii=False, indent=2,
                    )

                partition_infos = []
                for partition in sorted(partitions):
                    tp = TopicPartition(topic_name, partition)
                    # Get partition metadata
                    meta = consumer._client.cluster
                    leader = meta.leader_for_partition(tp)
                    available = meta.epochs_for_partition(tp) is not None if hasattr(meta, 'epochs_for_partition') else True

                    # Get end offset
                    try:
                        end_offsets = consumer.end_offsets([tp])
                        end_offset = end_offsets.get(tp, 0)
                    except Exception:
                        end_offset = -1

                    partition_infos.append({
                        "partition": partition,
                        "leader": leader if leader is not None else -1,
                        "end_offset": end_offset,
                    })

                # Get topic config (if available)
                topic_config = {}
                try:
                    from kafka.admin import KafkaAdminClient, ConfigResource, ConfigResourceType
                    admin = KafkaAdminClient(
                        bootstrap_servers=pool.bootstrap_servers,
                        request_timeout_ms=10000,
                    )
                    try:
                        resources = [ConfigResource(ConfigResourceType.TOPIC, topic_name)]
                        configs = admin.describe_configs(resources)
                        if configs:
                            for cfg in configs:
                                if hasattr(cfg, 'resources') and cfg.resources:
                                    for res in cfg.resources:
                                        if hasattr(res, 'config_value'):
                                            topic_config[res.config_name] = res.config_value
                    finally:
                        admin.close()
                except Exception:
                    pass

                result = {
                    "topic": topic_name,
                    "partition_count": len(partitions),
                    "partitions": partition_infos,
                    "config": topic_config if topic_config else None,
                }

                return json.dumps(result, ensure_ascii=False, indent=2, default=str)
            finally:
                consumer.close(autocommit=False)

        except Exception as e:
            return f"获取 topic '{topic_name}' 信息失败: {str(e)}"

