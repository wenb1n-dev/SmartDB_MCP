"""Elasticsearch health check handler.

Provides comprehensive health diagnostics for Elasticsearch clusters,
covering cluster health, shard status, thread pools, and segment merges.
"""

import json

from connection.pool_manager import MultiDBPoolManager


class ElasticsearchHealth:
    """Elasticsearch health check handler.

    Supports the following health_type values:
    - ``all``: full diagnostics
    - ``cluster``: cluster health and status
    - ``shards``: shard status and allocation
    - ``thread_pool``: thread pool queues and rejections
    - ``segments``: segment counts and merge operations
    """

    def get_db_health(self, pool_name: str, health_type: str = "all") -> str:
        """Get Elasticsearch health status.

        Args:
            pool_name: Connection pool name.
            health_type: Type of health check to perform.

        Returns:
            Formatted health report string.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        with pool.connection() as client:
            sections = []

            if health_type in ("all", "cluster"):
                sections.append(self._check_cluster(client))
            if health_type in ("all", "shards"):
                sections.append(self._check_shards(client))
            if health_type in ("all", "thread_pool"):
                sections.append(self._check_thread_pool(client))
            if health_type in ("all", "segments"):
                sections.append(self._check_segments(client))

            return "\n\n".join(sections)

    def _check_cluster(self, client) -> str:
        """Check cluster health and status."""
        try:
            health = client.cluster.health()
            lines = [
                "=== 集群健康诊断 ===",
                f"cluster_name: {health.get('cluster_name', 'N/A')}",
                f"status: {health.get('status', 'N/A')}",
                f"number_of_nodes: {health.get('number_of_nodes', 'N/A')}",
                f"number_of_data_nodes: {health.get('number_of_data_nodes', 'N/A')}",
                f"active_primary_shards: {health.get('active_primary_shards', 'N/A')}",
                f"active_shards: {health.get('active_shards', 'N/A')}",
                f"relocating_shards: {health.get('relocating_shards', 'N/A')}",
                f"initializing_shards: {health.get('initializing_shards', 'N/A')}",
                f"unassigned_shards: {health.get('unassigned_shards', 'N/A')}",
                f"pending_tasks: {health.get('number_of_pending_tasks', 'N/A')}",
            ]

            status = health.get("status", "")
            if status == "red":
                lines.append("⚠️ 警告: 集群状态为 RED，存在未分配的主分片")
            elif status == "yellow":
                lines.append("⚠️ 警告: 集群状态为 YELLOW，存在未分配的副本分片")

            return "\n".join(lines)
        except Exception as e:
            return f"=== 集群健康诊断 ===\n获取集群健康信息失败: {str(e)}"

    def _check_shards(self, client) -> str:
        """Check shard status and allocation."""
        try:
            # Use cat shards API for concise shard info
            shards = client.cat.shards(format="json", s="index")
            if not shards:
                return "=== 分片诊断 ===\n无分片信息"

            # Aggregate by status
            status_counts = {}
            unassigned = []
            for shard in shards:
                state = shard.get("state", "unknown")
                status_counts[state] = status_counts.get(state, 0) + 1
                if state in ("UNASSIGNED", "RELOCATING", "INITIALIZING"):
                    idx = shard.get("index", "N/A")
                    shard_num = shard.get("shard", "N/A")
                    reason = shard.get("unassigned.reason", "")
                    unassigned.append(f"  - {idx}[{shard_num}]: {state} {reason}")

            lines = ["=== 分片诊断 ===", f"总分片数: {len(shards)}"]
            for state, count in sorted(status_counts.items()):
                lines.append(f"  {state}: {count}")

            if unassigned:
                lines.append(f"\n异常分片 ({len(unassigned)}):")
                lines.extend(unassigned[:20])

            return "\n".join(lines)
        except Exception as e:
            return f"=== 分片诊断 ===\n获取分片信息失败: {str(e)}"

    def _check_thread_pool(self, client) -> str:
        """Check thread pool queues and rejections."""
        try:
            stats = client.nodes.stats(metric="thread_pool")
            nodes = stats.get("nodes", {})
            if not nodes:
                return "=== 线程池诊断 ===\n无节点信息"

            lines = ["=== 线程池诊断 ==="]
            for node_id, node_info in nodes.items():
                node_name = node_info.get("name", node_id)
                thread_pools = node_info.get("thread_pool", {})
                lines.append(f"\n节点: {node_name}")

                for pool_name in ["search", "write", "get", "analyze"]:
                    pool = thread_pools.get(pool_name, {})
                    queue = pool.get("queue", 0)
                    rejected = pool.get("rejected", 0)
                    active = pool.get("active", 0)
                    threads = pool.get("threads", 0)
                    lines.append(
                        f"  {pool_name}: active={active}, threads={threads}, "
                        f"queue={queue}, rejected={rejected}"
                    )
                    if rejected > 0:
                        lines.append(f"    ⚠️ 警告: {pool_name} 线程池有 {rejected} 次拒绝")

            return "\n".join(lines)
        except Exception as e:
            return f"=== 线程池诊断 ===\n获取线程池信息失败: {str(e)}"

    def _check_segments(self, client) -> str:
        """Check segment counts and merge operations."""
        try:
            stats = client.indices.stats(metric="segments,merges")
            primaries = stats.get("primaries", {})
            seg_stats = primaries.get("segments", {})
            merge_stats = primaries.get("merges", {})

            lines = [
                "=== 段与合并诊断 ===",
                f"count: {seg_stats.get('count', 'N/A')}",
                f"memory_in_bytes: {seg_stats.get('memory_in_bytes', 'N/A')}",
                f"terms_memory_in_bytes: {seg_stats.get('terms_memory_in_bytes', 'N/A')}",
                f"stored_fields_memory_in_bytes: {seg_stats.get('stored_fields_memory_in_bytes', 'N/A')}",
            ]

            if merge_stats:
                lines.extend([
                    f"\n合并统计:",
                    f"current: {merge_stats.get('current', 'N/A')}",
                    f"current_docs: {merge_stats.get('current_docs', 'N/A')}",
                    f"current_size_in_bytes: {merge_stats.get('current_size_in_bytes', 'N/A')}",
                    f"total: {merge_stats.get('total', 'N/A')}",
                    f"total_time_in_millis: {merge_stats.get('total_time_in_millis', 'N/A')}ms",
                ])

            return "\n".join(lines)
        except Exception as e:
            return f"=== 段与合并诊断 ===\n获取段信息失败: {str(e)}"

    def get_prompt(self, results: str, db_version: str, db_type: str = "") -> str:
        """Generate Elasticsearch-specific diagnostic prompt."""
        return f"""# 角色
                你是一位精通 Elasticsearch 和各类搜索引擎的专家，拥有超过 10 年的 Elasticsearch 运维和性能调优经验，
                负责根据给定的 ES 健康数据进行分析和诊断。
                你熟悉：
                - Elasticsearch 集群架构与分片分配
                - 索引设计与 Mapping 优化
                - 段合并与存储管理
                - 线程池调优与请求队列
                - 查询 DSL 优化与聚合性能
                - 热点线程与 CPU/内存瓶颈排查

                # 背景
                - 数据库类型: Elasticsearch
                - 数据库版本号:
                {db_version}

                {results}

                # 任务
                - 仔细评估提供的 Elasticsearch 健康数据，提供诊断报告和解决方案。

                # 分析要求（结构化输出）
                ## Elasticsearch 健康状态诊断报告
                -----
                ### 1.【版本信息】

                ### 2.【整体健康评估】
                - 判断当前是否存在严重问题（集群 RED、分片未分配、线程池拒绝、段合并堆积等）
                - 给出健康等级：🟢 健康 / 🟡 警告 / 🔴 严重

                ### 3. 【分项诊断】
                按以下维度分析（仅输出存在的数据，若无对应数据则提示未提供）：
                - **集群状态**：集群健康、节点数、主分片/副本分片状态
                - **分片状态**：活跃/未分配分片、分片迁移
                - **线程池**：search/write/get 线程池队列、拒绝数
                - **段与合并**：段数量、内存占用、合并进度

                ### 4. 【根因分析】
                结合 ES 行为推断根本原因，例如：
                - 分片数过少导致热点
                - Mapping 不合理导致字段爆炸
                - 线程池队列堆积导致请求超时
                - 段过多导致查询性能下降

                ### 5. 【解决方案建议】
                提供 Elasticsearch 专属的可执行建议：
                - ✅ **优化建议**：如"增加副本分片"、"优化 Mapping"
                - 💡 **DSL 示例**：使用 ES 查询语法
                - ⚙️ **配置建议**：如 `indices.query.bool.max_clause_count`、线程池大小
                - 📊 **监控建议**：建议监控集群健康、分片分配

                ### 6. 【风险提示】
                - 标注操作风险等级（低/中/高）
                - 提示生产环境需备份、评估影响

                ## 输出要求
                - 使用清晰的 Markdown 结构
                - 所有建议必须基于输入数据，避免臆测
                - 若信息不足，请明确指出："需补充以下信息：..."""

