"""MongoDB health check handler.

Provides basic health check implementation. Full diagnostic coverage
is implemented in Task 3.4.
"""

from connection.pool_manager import MultiDBPoolManager


class MongoDBHealth:
    """MongoDB health check handler.

    Supports the following health_type values:
    - ``all``: full diagnostics
    - ``connection``: connection and server info
    - ``memory``: memory and storage usage
    - ``slowlog``: slow operations (if available)
    - ``replication``: replica set status
    - ``indexes``: index statistics
    """

    def get_db_health(self, pool_name: str, health_type: str = "all") -> str:
        """Get MongoDB health status.

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
                sections.append(self._check_memory(client, pool_name))
            if health_type in ("all", "slowlog"):
                sections.append(self._check_slowlog(client))
            if health_type in ("all", "replication"):
                sections.append(self._check_replication(client))
            if health_type in ("all", "indexes"):
                sections.append(self._check_indexes(client, pool_name))

            return "\n\n".join(sections)

    def _check_connection(self, client) -> str:
        """Check connection and server info."""
        try:
            info = client.server_info()
            lines = [
                "=== 连接诊断 ===",
                f"version: {info.get('version', 'N/A')}",
                f"host: {info.get('host', 'N/A')}",
                f"process: {info.get('process', 'N/A')}",
                f"pid: {info.get('pid', 'N/A')}",
                f"uptime: {info.get('uptime', 'N/A')}s",
                f"storage_engine: {info.get('storageEngine', {}).get('name', 'N/A')}",
            ]
            return "\n".join(lines)
        except Exception as e:
            return f"=== 连接诊断 ===\n获取服务器信息失败: {str(e)}"

    def _check_memory(self, client, pool_name: str) -> str:
        """Check memory and storage usage."""
        try:
            from config.dbconfig import get_db_config_by_name
            config = get_db_config_by_name(pool_name)
            db_name = config.get("database", "admin")

            db = client[db_name]
            db_stats = db.command("dbstats")

            lines = [
                "=== 内存与存储诊断 ===",
                f"database: {db_name}",
                f"dataSize: {db_stats.get('dataSize', 'N/A')}",
                f"storageSize: {db_stats.get('storageSize', 'N/A')}",
                f"indexSize: {db_stats.get('indexSize', 'N/A')}",
                f"collections: {db_stats.get('collections', 'N/A')}",
                f"objects: {db_stats.get('objects', 'N/A')}",
            ]

            # Server status for memory info
            try:
                server_status = db.command("serverStatus")
                mem = server_status.get("mem", {})
                lines.extend([
                    f"resident: {mem.get('resident', 'N/A')} MB",
                    f"virtual: {mem.get('virtual', 'N/A')} MB",
                    f"mapped: {mem.get('mapped', 'N/A')} MB",
                ])
            except Exception:
                lines.append("(serverStatus 不可用，可能权限不足)")

            return "\n".join(lines)
        except Exception as e:
            return f"=== 内存与存储诊断 ===\n获取内存信息失败: {str(e)}"

    def _check_slowlog(self, client) -> str:
        """Check slow operations via $currentOp."""
        try:
            from pymongo import ASCENDING
            db = client["admin"]
            # Use $currentOp to find long-running operations
            pipeline = [
                {"$currentOp": {"allUsers": True, "idleCursors": True}},
                {"$match": {"secs_running": {"$gte": 1}}},
                {"$sort": {"secs_running": -1}},
                {"$limit": 10},
            ]
            slow_ops = list(db.aggregate(pipeline))

            if not slow_ops:
                return "=== 慢查询诊断 ===\n无慢查询记录"

            lines = [f"=== 慢查询诊断 ===\n最近 {len(slow_ops)} 条慢查询:"]
            for op in slow_ops:
                op_type = op.get("op", "unknown")
                secs = op.get("secs_running", 0)
                ns = op.get("ns", "N/A")
                command = op.get("command", {})
                cmd_name = list(command.keys())[0] if isinstance(command, dict) and command else "unknown"
                lines.append(f"  - 类型: {op_type}, 命名空间: {ns}, 命令: {cmd_name}, 运行时间: {secs}s")

            return "\n".join(lines)
        except Exception as e:
            return f"=== 慢查询诊断 ===\n获取慢查询失败: {str(e)}"

    def _check_replication(self, client) -> str:
        """Check replica set status."""
        try:
            status = client.admin.command("replSetGetStatus")
            lines = [
                "=== 复制诊断 ===",
                f"set: {status.get('set', 'N/A')}",
                f"date: {status.get('date', 'N/A')}",
            ]

            my_state = status.get("myState", -1)
            state_map = {0: "startup", 1: "primary", 2: "secondary", 3: "recovering",
                        4: "fatal", 5: "startup2", 6: "unknown", 7: "arbiter",
                        8: "down", 9: "rollback", 10: "removed"}
            lines.append(f"myState: {my_state} ({state_map.get(my_state, 'unknown')})")

            members = status.get("members", [])
            lines.append(f"members: {len(members)}")
            for m in members:
                name = m.get("name", "N/A")
                state = m.get("stateStr", "N/A")
                health = m.get("health", -1)
                health_str = "UP" if health == 1 else "DOWN"
                lines.append(f"  - {name}: state={state}, health={health_str}")

            return "\n".join(lines)
        except Exception as e:
            err_str = str(e)
            if "not running with --replSet" in err_str or "no replset" in err_str.lower():
                return "=== 复制诊断 ===\n当前 MongoDB 实例未启用副本集 (standalone 模式)"
            return f"=== 复制诊断 ===\n获取复制状态失败: {err_str}"

    def _check_indexes(self, client, pool_name: str) -> str:
        """Check index statistics for all collections."""
        try:
            from config.dbconfig import get_db_config_by_name
            config = get_db_config_by_name(pool_name)
            db_name = config.get("database", "admin")

            db = client[db_name]
            lines = [f"=== 索引诊断 ===\n数据库: {db_name}"]

            for coll_info in db.list_collections():
                coll_name = coll_info["name"]
                coll = db[coll_name]
                indexes = list(coll.list_indexes())
                lines.append(f"\n集合 '{coll_name}': {len(indexes)} 个索引")
                for idx in indexes:
                    idx_name = idx.get("name", "N/A")
                    keys = idx.get("key", {})
                    key_str = ", ".join(f"{k}:{v}" for k, v in keys.items())
                    lines.append(f"  - {idx_name}: {key_str}")

            return "\n".join(lines)
        except Exception as e:
            return f"=== 索引诊断 ===\n获取索引信息失败: {str(e)}"
