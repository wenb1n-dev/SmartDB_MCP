"""Kafka consumer groups and lag handler.

Queries consumer group information and lag (offset difference between
topic end and consumer position).
"""

import json
from typing import Optional

from connection.pool_manager import MultiDBPoolManager
from datasource.base import Paradigm
from permission.enforcer import enforcer


class KafkaConsumerGroups:
    """Query consumer group info and lag for Kafka."""

    def get_consumer_lag(
        self,
        pool_name: str,
        group_id: Optional[str] = None,
    ) -> str:
        """Get consumer group lag information.

        Args:
            pool_name: Connection pool name.
            group_id: Specific consumer group ID. If None, lists all groups.

        Returns:
            JSON-formatted consumer lag info.
        """
        # 统一鉴权入口：消费者组读取按目标执行池鉴权
        operation_key = "DESCRIBE_GROUP" if group_id else "LIST_GROUPS"
        enforcer.authorize_category(
            pool_name,
            operation_key,
            Paradigm.MESSAGE_QUEUE,
            tool="get_consumer_lag",
        ).raise_if_denied()

        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        try:
            from kafka import KafkaAdminClient, TopicPartition
            from kafka.consumer.group import KafkaConsumer

            admin = KafkaAdminClient(
                bootstrap_servers=pool.bootstrap_servers,
                request_timeout_ms=10000,
            )
            try:
                if group_id:
                    return self._get_single_group_lag(pool, admin, group_id)
                else:
                    return self._get_all_groups_lag(pool, admin)
            finally:
                admin.close()

        except Exception as e:
            return f"获取消费者延迟信息失败: {str(e)}"

    def _get_all_groups_lag(self, pool, admin) -> str:
        """Get lag for all consumer groups."""
        try:
            groups = admin.list_consumer_groups()
            if not groups:
                return json.dumps(
                    {"total_groups": 0, "groups": [], "message": "没有消费者组"},
                    ensure_ascii=False, indent=2,
                )

            result = {
                "total_groups": len(groups),
                "groups": [],
            }

            for group_name, protocol_type in groups[:50]:  # Limit to 50 groups
                try:
                    lag_info = self._compute_group_lag(pool, group_name)
                    result["groups"].append(lag_info)
                except Exception as e:
                    result["groups"].append({
                        "group_id": group_name,
                        "error": str(e),
                    })

            return json.dumps(result, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            return f"获取所有消费者组信息失败: {str(e)}"

    def _get_single_group_lag(self, pool, admin, group_id: str) -> str:
        """Get lag for a single consumer group."""
        try:
            lag_info = self._compute_group_lag(pool, group_id)
            return json.dumps(lag_info, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            return f"获取消费者组 '{group_id}' 信息失败: {str(e)}"

    def _compute_group_lag(self, pool, group_id: str) -> dict:
        """Compute lag for a consumer group."""
        from kafka import TopicPartition
        from kafka.consumer.group import KafkaConsumer

        consumer = KafkaConsumer(
            bootstrap_servers=pool.bootstrap_servers,
            group_id=group_id,
            request_timeout_ms=10000,
            enable_auto_commit=False,
            consumer_timeout_ms=5000,
        )
        try:
            # Get partitions assigned to this group
            assignment = consumer.assignment()
            if not assignment:
                # Try to get topics the group is consuming
                topics = list(consumer.topics())
                assignment = set()
                for topic in topics[:10]:  # Limit topics
                    partitions = consumer.partitions_for_topic(topic)
                    if partitions:
                        for p in partitions:
                            assignment.add(TopicPartition(topic, p))

            # Get end offsets (latest)
            if assignment:
                end_offsets = consumer.end_offsets(list(assignment))
                # Get committed offsets
                committed = consumer.committed()

                total_lag = 0
                partition_lags = []
                for tp in sorted(assignment, key=lambda x: (x.topic, x.partition)):
                    end_offset = end_offsets.get(tp, 0)
                    committed_offset = committed.get(tp, 0) if committed else 0
                    if committed_offset is None:
                        committed_offset = 0
                    lag = max(0, end_offset - committed_offset)
                    total_lag += lag
                    partition_lags.append({
                        "topic": tp.topic,
                        "partition": tp.partition,
                        "committed_offset": committed_offset,
                        "end_offset": end_offset,
                        "lag": lag,
                    })

                return {
                    "group_id": group_id,
                    "total_partitions": len(assignment),
                    "total_lag": total_lag,
                    "partitions": partition_lags[:100],  # Limit output
                }
            else:
                return {
                    "group_id": group_id,
                    "total_partitions": 0,
                    "total_lag": 0,
                    "message": "消费者组没有活跃的分区分配",
                }
        finally:
            consumer.close(autocommit=False)
