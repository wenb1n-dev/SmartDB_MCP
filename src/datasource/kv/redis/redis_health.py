"""Redis health check handler.

Provides basic health check implementation. Full diagnostic coverage
is implemented in Task 2.5.
"""

from connection.pool_manager import MultiDBPoolManager


class RedisHealth:
    """Redis health check handler.

    Supports the following health_type values:
    - ``all``: full diagnostics
    - ``connection``: connection and client info
    - ``memory``: memory usage and fragmentation
    - ``slowlog``: slow query log
    - ``replication``: replication status
    - ``persistence``: RDB/AOF persistence status
    """

    def get_db_health(self, pool_name: str, health_type: str = "all") -> str:
        """Get Redis health status.

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

            if health_type in ("all", "connection"):
                sections.append(self._check_connection(client))
            if health_type in ("all", "memory"):
                sections.append(self._check_memory(client))
            if health_type in ("all", "slowlog"):
                sections.append(self._check_slowlog(client))
            if health_type in ("all", "replication"):
                sections.append(self._check_replication(client))
            if health_type in ("all", "persistence"):
                sections.append(self._check_persistence(client))

            return "\n\n".join(sections)

    def _check_connection(self, client) -> str:
        """Check connection and client info."""
        info = client.info("clients")
        server_info = client.info("server")
        lines = [
            "=== 连接诊断 ===",
            f"connected_clients: {info.get('connected_clients', 'N/A')}",
            f"blocked_clients: {info.get('blocked_clients', 'N/A')}",
            f"maxclients: {server_info.get('maxclients', 'N/A')}",
            f"total_connections_received: {info.get('total_connections_received', 'N/A')}",
            f"rejected_connections: {info.get('rejected_connections', 'N/A')}",
        ]
        return "\n".join(lines)

    def _check_memory(self, client) -> str:
        """Check memory usage."""
        info = client.info("memory")
        used_memory = info.get("used_memory_human", "N/A")
        used_memory_peak = info.get("used_memory_peak_human", "N/A")
        maxmemory = info.get("maxmemory_human", "0B")
        maxmemory_policy = info.get("maxmemory_policy", "noeviction")
        mem_fragmentation_ratio = info.get("mem_fragmentation_ratio", "N/A")

        lines = [
            "=== 内存诊断 ===",
            f"used_memory: {used_memory}",
            f"used_memory_peak: {used_memory_peak}",
            f"maxmemory: {maxmemory}",
            f"maxmemory_policy: {maxmemory_policy}",
            f"mem_fragmentation_ratio: {mem_fragmentation_ratio}",
        ]

        # Warning for high fragmentation
        try:
            ratio = float(mem_fragmentation_ratio)
            if ratio > 1.5:
                lines.append(f"⚠️ 警告: 内存碎片率 {ratio} 偏高，建议检查是否需要重启或使用 MEMORY PURGE")
        except (ValueError, TypeError):
            pass

        return "\n".join(lines)

    def _check_slowlog(self, client) -> str:
        """Check slow query log."""
        slowlog = client.slowlog_get(10)
        if not slowlog:
            return "=== 慢查询诊断 ===\n无慢查询记录"

        lines = ["=== 慢查询诊断 ===", f"最近 {len(slowlog)} 条慢查询:"]
        for entry in slowlog:
            command = entry.get("command", "unknown")
            if isinstance(command, bytes):
                command = command.decode("utf-8", errors="replace")
            duration_us = entry.get("duration", 0)
            duration_ms = duration_us / 1000
            lines.append(f"  - 命令: {command}, 耗时: {duration_ms:.2f}ms")

        return "\n".join(lines)

    def _check_replication(self, client) -> str:
        """Check replication status."""
        info = client.info("replication")
        role = info.get("role", "unknown")

        lines = [
            "=== 复制诊断 ===",
            f"role: {role}",
        ]

        if role == "master":
            connected_slaves = info.get("connected_slaves", 0)
            lines.append(f"connected_slaves: {connected_slaves}")
            for i in range(connected_slaves):
                key = f"slave{i}"
                if key in info:
                    lines.append(f"  {key}: {info[key]}")
        elif role == "slave":
            master_host = info.get("master_host", "N/A")
            master_port = info.get("master_port", "N/A")
            master_link_status = info.get("master_link_status", "N/A")
            master_last_io_seconds_ago = info.get("master_last_io_seconds_ago", "N/A")
            slave_repl_offset = info.get("slave_repl_offset", "N/A")
            lines.extend([
                f"master_host: {master_host}",
                f"master_port: {master_port}",
                f"master_link_status: {master_link_status}",
                f"master_last_io_seconds_ago: {master_last_io_seconds_ago}",
                f"slave_repl_offset: {slave_repl_offset}",
            ])
            if master_link_status != "up":
                lines.append("⚠️ 警告: 主从连接状态异常")

        return "\n".join(lines)

    def _check_persistence(self, client) -> str:
        """Check RDB/AOF persistence status."""
        info = client.info("persistence")
        lines = ["=== 持久化诊断 ==="]

        # RDB status
        rdb_bgsave_in_progress = info.get("rdb_bgsave_in_progress", 0)
        rdb_last_save_time = info.get("rdb_last_save_time", 0)
        rdb_last_bgsave_status = info.get("rdb_last_bgsave_status", "unknown")
        lines.extend([
            f"rdb_bgsave_in_progress: {rdb_bgsave_in_progress}",
            f"rdb_last_save_time: {rdb_last_save_time}",
            f"rdb_last_bgsave_status: {rdb_last_bgsave_status}",
        ])

        # AOF status
        aof_enabled = info.get("aof_enabled", 0)
        if aof_enabled:
            aof_rewrite_in_progress = info.get("aof_rewrite_in_progress", 0)
            aof_last_rewrite_time_sec = info.get("aof_last_rewrite_time_sec", -1)
            aof_last_bgrewrite_status = info.get("aof_last_bgrewrite_status", "unknown")
            lines.extend([
                f"aof_enabled: {aof_enabled}",
                f"aof_rewrite_in_progress: {aof_rewrite_in_progress}",
                f"aof_last_rewrite_time_sec: {aof_last_rewrite_time_sec}",
                f"aof_last_bgrewrite_status: {aof_last_bgrewrite_status}",
            ])
        else:
            lines.append("aof_enabled: 0 (AOF 未启用)")

        if rdb_last_bgsave_status != "ok":
            lines.append("⚠️ 警告: 最近一次 RDB 保存状态异常")

        return "\n".join(lines)

    def get_prompt(self, results: str, db_version: str, db_type: str = "") -> str:
        """Generate Redis-specific diagnostic prompt."""
        return f"""# 角色
                你是一位精通 Redis 和各类内存数据库的专家，拥有超过 15 年的 Redis 运维和性能调优经验，
                负责根据给定的 Redis 健康数据进行分析和诊断。
                你熟悉：
                - Redis 内存管理与淘汰策略
                - 主从复制与哨兵/集群架构
                - 持久化机制（RDB/AOF）与性能影响
                - 慢查询分析与优化
                - 连接管理与客户端问题排查
                - 大 Key/热 Key 识别与处理

                # 背景
                - 数据库类型: Redis
                - 数据库版本号:
                {db_version}

                {results}

                # 任务
                - 仔细评估提供的 Redis 健康数据，提供诊断报告和解决方案。

                # 分析要求（结构化输出）
                ## Redis 健康状态诊断报告
                -----
                ### 1.【版本信息】

                ### 2.【整体健康评估】
                - 判断当前是否存在严重问题（内存溢出、连接耗尽、主从断开、慢查询堆积等）
                - 给出健康等级：🟢 健康 / 🟡 警告 / 🔴 严重

                ### 3. 【分项诊断】
                按以下维度分析（仅输出存在的数据，若无对应数据则提示未提供）：
                - **连接问题**：连接数、拒绝连接、阻塞客户端
                - **内存问题**：内存使用、碎片率、淘汰策略、OOM 风险
                - **持久化问题**：RDB/AOF 状态、保存耗时
                - **慢查询**：慢查询数量、耗时、命令类型
                - **复制状态**：主从连接、延迟、偏移量

                ### 4. 【根因分析】
                结合 Redis 行为推断根本原因，例如：
                - 大 Key 导致内存增长
                - 连接泄漏导致连接数耗尽
                - 持久化频率过高导致性能下降
                - 缺少过期策略导致内存膨胀

                ### 5. 【解决方案建议】
                提供 Redis 专属的可执行建议：
                - ✅ **优化建议**：如"拆分大 Key"、"设置合理过期时间"
                - 💡 **命令示例**：使用 Redis 语法
                - ⚙️ **配置建议**：如 `maxmemory-policy`、`save` 配置
                - 📊 **监控建议**：建议开启慢查询日志、设置告警

                ### 6. 【风险提示】
                - 标注操作风险等级（低/中/高）
                - 提示生产环境需备份、评估影响

                ## 输出要求
                - 使用清晰的 Markdown 结构
                - 所有建议必须基于输入数据，避免臆测
                - 若信息不足，请明确指出："需补充以下信息：..."""

