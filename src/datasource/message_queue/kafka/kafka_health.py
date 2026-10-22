"""Kafka health check handler.

Provides comprehensive health diagnostics for Kafka clusters,
covering broker status, partition leaders, ISR, and consumer lag.
"""

from connection.pool_manager import MultiDBPoolManager


class KafkaHealth:
    """Kafka health check handler.

    Supports the following health_type values:
    - ``all``: full diagnostics
    - ``brokers``: broker status and connectivity
    - ``topics``: topic and partition status
    - ``isr``: ISR (In-Sync Replicas) health
    - ``lag``: consumer group lag
    """

    def get_db_health(self, pool_name: str, health_type: str = "all") -> str:
        """Get Kafka health status.

        Args:
            pool_name: Connection pool name.
            health_type: Type of health check to perform.

        Returns:
            Formatted health report string.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        sections = []

        if health_type in ("all", "brokers"):
            sections.append(self._check_brokers(pool))
        if health_type in ("all", "topics"):
            sections.append(self._check_topics(pool))
        if health_type in ("all", "isr"):
            sections.append(self._check_isr(pool))
        if health_type in ("all", "lag"):
            sections.append(self._check_lag(pool))

        return "\n\n".join(sections)

    def _check_brokers(self, pool) -> str:
        """Check broker status and connectivity.

        通过高层 API ``describe_cluster()`` 获取 broker 列表与 controller，
        兼容 kafka-python-ng（其 BrokerMetadata 字段为 nodeId，且
        ClusterMetadata 不再提供 controller() 方法）。
        """
        try:
            with pool.connection() as admin:
                cluster = admin.describe_cluster()

            brokers = cluster.get("brokers", [])
            controller_id = cluster.get("controller_id")

            lines = [
                "=== Broker 状态诊断 ===",
                f"broker_count: {len(brokers)}",
                f"controller_id: {controller_id}",
            ]

            for broker in brokers:
                node_id = broker.get("node_id")
                is_controller = node_id == controller_id
                lines.append(
                    f"  broker {node_id}: {broker.get('host')}:{broker.get('port')}"
                    f"{' (controller)' if is_controller else ''}"
                )

            if len(brokers) == 0:
                lines.append("⚠️ 警告: 没有可用的 broker")

            return "\n".join(lines)
        except Exception as e:
            return f"=== Broker 状态诊断 ===\n获取 broker 信息失败: {str(e)}"

    def _check_topics(self, pool) -> str:
        """Check topic and partition status.

        通过 ``describe_topics()`` 统计业务 topic（排除内部 topic）、
        分区总数以及无 Leader（leader 为 -1/None）的分区数。
        """
        try:
            with pool.connection() as admin:
                topics_meta = admin.describe_topics(topics=None)

            user_topics = [t for t in topics_meta if not t.get("is_internal")]
            total_partitions = 0
            no_leader_partitions = 0

            for topic in user_topics:
                for partition in topic.get("partitions", []):
                    total_partitions += 1
                    leader = partition.get("leader")
                    if leader is None or leader == -1:
                        no_leader_partitions += 1

            lines = [
                "=== Topic 与分区诊断 ===",
                f"total_topics: {len(user_topics)}",
                f"total_partitions: {total_partitions}",
                f"no_leader_partitions: {no_leader_partitions}",
            ]
            if no_leader_partitions > 0:
                lines.append(f"⚠️ 警告: {no_leader_partitions} 个分区无 Leader")

            return "\n".join(lines)
        except Exception as e:
            return f"=== Topic 与分区诊断 ===\n获取 topic 信息失败: {str(e)}"

    def _check_isr(self, pool) -> str:
        """Check ISR (In-Sync Replicas) health.

        通过 ``describe_topics()`` 返回的每个分区的 leader / replicas / isr /
        offline_replicas 字段，统计无 Leader、ISR 缩减及存在离线副本的分区。
        """
        try:
            with pool.connection() as admin:
                topics_meta = admin.describe_topics(topics=None)

            user_topics = [t for t in topics_meta if not t.get("is_internal")]

            partitions_checked = 0
            no_leader = 0
            under_replicated = 0
            offline_replica_partitions = 0

            for topic in user_topics:
                for partition in topic.get("partitions", []):
                    partitions_checked += 1
                    replicas = partition.get("replicas", []) or []
                    isr = partition.get("isr", []) or []
                    offline = partition.get("offline_replicas", []) or []
                    leader = partition.get("leader")

                    if leader is None or leader == -1:
                        no_leader += 1
                    if len(isr) < len(replicas):
                        under_replicated += 1
                    if offline:
                        offline_replica_partitions += 1

            lines = [
                "=== ISR 健康诊断 ===",
                f"checked_topics: {len(user_topics)}",
                f"partitions_checked: {partitions_checked}",
                f"no_leader_partitions: {no_leader}",
                f"under_replicated_partitions: {under_replicated}",
                f"offline_replica_partitions: {offline_replica_partitions}",
            ]

            if no_leader > 0:
                lines.append(f"⚠️ 警告: {no_leader} 个分区无 Leader")
            if under_replicated > 0:
                lines.append(f"⚠️ 警告: {under_replicated} 个分区 ISR 缩减（未充分同步）")
            if offline_replica_partitions > 0:
                lines.append(f"⚠️ 警告: {offline_replica_partitions} 个分区存在离线副本")

            return "\n".join(lines)
        except Exception as e:
            return f"=== ISR 健康诊断 ===\n获取 ISR 信息失败: {str(e)}"

    @staticmethod
    def _get_group_field(info, field: str, default=None):
        """从 describe_consumer_groups 的结果元素中兼容地取字段。

        不同 kafka 客户端版本可能返回 dict、namedtuple 或普通对象，
        这里依次尝试 dict 索引、属性访问。
        """
        if info is None:
            return default
        if isinstance(info, dict):
            return info.get(field, default)
        return getattr(info, field, default)

    def _check_lag(self, pool) -> str:
        """Check consumer group count and member status."""
        try:
            with pool.connection() as admin:
                groups = admin.list_consumer_groups()
                lines = [
                    "=== 消费者延迟诊断 ===",
                    f"consumer_groups: {len(groups)}",
                ]

                # list_consumer_groups 返回 (group_id, protocol_type) 元组列表
                group_ids = [
                    g[0] if isinstance(g, (list, tuple)) else g for g in groups
                ]

                if not group_ids:
                    lines.append("（当前没有任何消费者组，无法评估 Lag）")
                    return "\n".join(lines)

                descriptions = admin.describe_consumer_groups(group_ids[:20])
                for info in descriptions:
                    group_id = self._get_group_field(
                        info, "group",
                        self._get_group_field(info, "group_id", "unknown"),
                    )
                    state = self._get_group_field(info, "state", "N/A")
                    members = self._get_group_field(info, "members", []) or []
                    lines.append(
                        f"  group: {group_id}, state: {state}, members: {len(members)}"
                    )

                return "\n".join(lines)
        except Exception as e:
            return f"=== 消费者延迟诊断 ===\n获取消费者组延迟信息失败: {str(e)}"

    def get_prompt(self, results: str, db_version: str, db_type: str = "") -> str:
        """Generate Kafka-specific diagnostic prompt."""
        return f"""# 角色
                你是一位精通 Kafka 和各类消息队列的专家，拥有超过 10 年的 Kafka 运维和性能调优经验，
                负责根据给定的 Kafka 健康数据进行分析和诊断。
                你熟悉：
                - Kafka 集群架构（Broker/Controller/Partition/Replica）
                - 分区与副本机制（Leader/Follower/ISR）
                - 消费者组与 Offset 管理
                - 生产者/消费者性能调优
                - 消息积压与 Lag 分析
                - 集群扩容与分区再平衡

                # 背景
                - 数据库类型: Kafka
                - 数据库版本号:
                {db_version}

                {results}

                # 任务
                - 仔细评估提供的 Kafka 健康数据，提供诊断报告和解决方案。

                # 分析要求（结构化输出）
                ## Kafka 健康状态诊断报告
                -----
                ### 1.【版本信息】

                ### 2.【整体健康评估】
                - 判断当前是否存在严重问题（Broker 宕机、分区无 Leader、ISR 缩减、消费者延迟过大等）
                - 给出健康等级：🟢 健康 / 🟡 警告 / 🔴 严重

                ### 3. 【分项诊断】
                按以下维度分析（仅输出存在的数据，若无对应数据则提示未提供）：
                - **Broker 状态**：Broker 数量、Controller、连通性
                - **Topic 与分区**：Topic 数量、分区数、无 Leader 分区
                - **ISR 健康**：同步副本数、未同步分区、副本缺失
                - **消费者延迟**：消费者组数量、Lag 大小、活跃消费者

                ### 4. 【根因分析】
                结合 Kafka 行为推断根本原因，例如：
                - Broker 资源不足导致分区无 Leader
                - 消费者处理速度跟不上生产速度导致积压
                - ISR 缩减导致数据可靠性降低
                - 分区数过少导致吞吐瓶颈

                ### 5. 【解决方案建议】
                提供 Kafka 专属的可执行建议：
                - ✅ **优化建议**：如"增加分区数"、"扩容消费者"
                - 💡 **命令示例**：使用 kafka-topics/kafka-consumer-groups 语法
                - ⚙️ **配置建议**：如 `num.partitions`、`default.replication.factor`、`fetch.max.bytes`
                - 📊 **监控建议**：建议监控 Lag、ISR、Broker 健康

                ### 6. 【风险提示】
                - 标注操作风险等级（低/中/高）
                - 提示生产环境需评估影响

                ## 输出要求
                - 使用清晰的 Markdown 结构
                - 所有建议必须基于输入数据，避免臆测
                - 若信息不足，请明确指出："需补充以下信息：..."""
