"""Milvus health check handler.

Provides comprehensive health diagnostics for Milvus vector database,
covering node status, index build progress, query latency, and memory usage.
"""

import json

from connection.pool_manager import MultiDBPoolManager


class MilvusHealth:
    """Milvus health check handler.

    Supports the following health_type values:
    - ``all``: full diagnostics
    - ``connection``: connection and server info
    - ``memory``: memory and storage usage
    - ``indexes``: index build progress and stats
    - ``latency``: query latency metrics
    - ``nodes``: cluster node status
    """

    def get_db_health(self, pool_name: str, health_type: str = "all") -> str:
        """Get Milvus health status.

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
            if health_type in ("all", "indexes"):
                sections.append(self._check_indexes(client))
            if health_type in ("all", "latency"):
                sections.append(self._check_latency(client))
            if health_type in ("all", "nodes"):
                sections.append(self._check_nodes(client))

            return "\n\n".join(sections)

    def _check_connection(self, client) -> str:
        """Check connection and server info."""
        try:
            version = client.get_server_version()
            lines = [
                "=== 连接诊断 ===",
                f"server_version: {version}",
            ]

            # Try to get collection count
            try:
                collections = client.list_collections()
                lines.append(f"collections: {len(collections)}")
                if collections:
                    lines.append(f"collection_names: {', '.join(collections[:20])}")
                    if len(collections) > 20:
                        lines.append(f"  ... and {len(collections) - 20} more")
            except Exception:
                lines.append("collections: (unable to list)")

            return "\n".join(lines)
        except Exception as e:
            return f"=== 连接诊断 ===\n获取服务器信息失败: {str(e)}"

    def _check_memory(self, client) -> str:
        """Check memory and storage usage."""
        try:
            from pymilvus import MilvusClient, utility
            from pymilvus.client import constants

            lines = ["=== 内存与存储诊断 ==="]

            # Get collection stats for storage estimation
            try:
                collections = client.list_collections()
                total_entities = 0
                lines.append(f"collections: {len(collections)}")

                for coll_name in collections[:10]:  # Limit to first 10
                    try:
                        stats = client.get_collection_stats(coll_name)
                        entity_count = stats.get("row_count", 0)
                        total_entities += int(entity_count) if entity_count else 0
                        lines.append(f"  {coll_name}: {entity_count} entities")
                    except Exception:
                        lines.append(f"  {coll_name}: (stats unavailable)")
            except Exception:
                lines.append("(unable to get collection stats)")

            lines.append(f"total_entities (sampled): {total_entities}")

            # Try to get metrics from Milvus
            try:
                # pymilvus utility.get_metrics may be available
                metrics = client.get_metrics(metric_type="system_info")
                if metrics:
                    lines.append(f"\nraw_metrics: {json.dumps(metrics, indent=2, default=str)[:500]}")
            except Exception:
                lines.append("(detailed metrics unavailable, may require admin privileges)")

            return "\n".join(lines)
        except Exception as e:
            return f"=== 内存与存储诊断 ===\n获取内存信息失败: {str(e)}"

    def _check_indexes(self, client) -> str:
        """Check index build progress and stats."""
        try:
            collections = client.list_collections()
            lines = [f"=== 索引诊断 ===\ncollections: {len(collections)}"]

            for coll_name in collections[:10]:
                try:
                    indexes = client.list_indexes(coll_name)
                    if indexes:
                        lines.append(f"\n集合 '{coll_name}': {len(indexes)} 个索引")
                        for idx in indexes:
                            idx_name = idx if isinstance(idx, str) else idx.get("index_name", "N/A")
                            lines.append(f"  - {idx_name}")
                    else:
                        lines.append(f"\n集合 '{coll_name}': 无索引")
                except Exception as e:
                    lines.append(f"\n集合 '{coll_name}': 获取索引失败 - {str(e)}")

            return "\n".join(lines)
        except Exception as e:
            return f"=== 索引诊断 ===\n获取索引信息失败: {str(e)}"

    def _check_latency(self, client) -> str:
        """Check query latency metrics."""
        try:
            lines = ["=== 查询延迟诊断 ==="]

            # Try a simple operation to measure latency
            import time
            start = time.time()
            try:
                client.list_collections()
                elapsed_ms = (time.time() - start) * 1000
                lines.append(f"list_collections latency: {elapsed_ms:.2f}ms")
            except Exception:
                lines.append("list_collections: failed")

            # Try to get metrics
            try:
                metrics = client.get_metrics(metric_type="system_latency")
                if metrics:
                    lines.append(f"\nraw_metrics: {json.dumps(metrics, indent=2, default=str)[:500]}")
            except Exception:
                lines.append("(detailed latency metrics unavailable)")

            return "\n".join(lines)
        except Exception as e:
            return f"=== 查询延迟诊断 ===\n获取延迟信息失败: {str(e)}"

    def _check_nodes(self, client) -> str:
        """Check cluster node status."""
        try:
            lines = ["=== 节点状态诊断 ==="]

            # Try to get replica info or node info
            try:
                collections = client.list_collections()
                for coll_name in collections[:3]:
                    try:
                        replicas = client.get_replicas(coll_name)
                        if replicas:
                            groups = replicas.get("groups", [])
                            lines.append(f"集合 '{coll_name}' 副本组: {len(groups)}")
                            for i, group in enumerate(groups):
                                members = group.get("group_nodes", [])
                                lines.append(f"  组 {i}: {len(members)} 个节点, ID: {members[:5]}")
                    except Exception:
                        pass
            except Exception:
                pass

            # Try metrics endpoint
            try:
                metrics = client.get_metrics(metric_type="node_info")
                if metrics:
                    lines.append(f"\nraw_node_metrics: {json.dumps(metrics, indent=2, default=str)[:500]}")
            except Exception:
                lines.append("(节点指标不可用，可能为单节点模式或权限不足)")

            if len(lines) == 1:
                lines.append("当前 Milvus 实例可能为单节点模式 (standalone)")

            return "\n".join(lines)
        except Exception as e:
            return f"=== 节点状态诊断 ===\n获取节点状态失败: {str(e)}"
