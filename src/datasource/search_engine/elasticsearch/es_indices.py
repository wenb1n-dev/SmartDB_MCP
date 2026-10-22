"""Elasticsearch index listing handler.

Lists indices in the Elasticsearch cluster, optionally filtered by pattern.
"""

import json
from typing import Optional

from connection.pool_manager import MultiDBPoolManager


class ElasticsearchIndices:
    """List indices in an Elasticsearch cluster."""

    def get_index_names(
        self,
        pool_name: str,
        pattern: Optional[str] = None,
    ) -> str:
        """List indices in the cluster.

        Args:
            pool_name: Connection pool name.
            pattern: Optional index name pattern (wildcard, e.g., "log-*").

        Returns:
            JSON-formatted index list.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        with pool.connection() as client:
            try:
                # Use cat indices API for concise index info
                if pattern:
                    indices = client.cat.indices(index=pattern, format="json", s="index")
                else:
                    indices = client.cat.indices(format="json", s="index")

                if not indices:
                    return json.dumps(
                        {"total_indices": 0, "indices": [], "message": "没有找到索引"},
                        ensure_ascii=False, indent=2,
                    )

                result = {
                    "total_indices": len(indices),
                    "indices": [],
                }

                for idx in indices:
                    result["indices"].append({
                        "index": idx.get("index", "N/A"),
                        "health": idx.get("health", "N/A"),
                        "status": idx.get("status", "N/A"),
                        "docs_count": idx.get("docs.count", "N/A"),
                        "docs_deleted": idx.get("docs.deleted", "N/A"),
                        "store_size": idx.get("store.size", "N/A"),
                        "pri": idx.get("pri", "N/A"),
                        "rep": idx.get("rep", "N/A"),
                    })

                return json.dumps(result, ensure_ascii=False, indent=2, default=str)

            except Exception as e:
                return f"获取索引列表失败: {str(e)}"
