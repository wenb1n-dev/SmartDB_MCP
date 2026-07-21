"""Milvus index info handler.

Queries index information on Milvus collections: index type (HNSW/IVF/DISKANN),
parameters, build progress, etc.
"""

import json
from typing import Optional

from connection.pool_manager import MultiDBPoolManager


class MilvusIndexInfo:
    """Query index information for Milvus vector collections."""

    def get_index_info(
        self,
        pool_name: str,
        collection: Optional[str] = None,
    ) -> str:
        """Get index information for one or all collections.

        Args:
            pool_name: Connection pool name.
            collection: Collection name. If None, lists indexes for all collections.

        Returns:
            JSON-formatted index information.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        with pool.connection() as client:
            try:
                if collection:
                    return self._get_indexes_for_collection(client, collection)
                else:
                    return self._get_indexes_for_all_collections(client)
            except Exception as e:
                return f"获取索引信息失败: {str(e)}"

    def _get_indexes_for_collection(self, client, collection: str) -> str:
        """Get index info for a single collection."""
        try:
            index_names = client.list_indexes(collection)

            if not index_names:
                result = {
                    "collection": collection,
                    "index_count": 0,
                    "message": "该集合没有索引 / Collection has no indexes",
                }
                return json.dumps(result, ensure_ascii=False, indent=2, default=str)

            result = {
                "collection": collection,
                "index_count": len(index_names),
                "indexes": [],
            }

            for idx_name in index_names:
                try:
                    desc = client.describe_index(collection, idx_name)
                    index_info = {
                        "index_name": idx_name,
                        "field_name": desc.get("field_name", "N/A"),
                        "index_type": desc.get("index_type", "N/A"),
                        "metric_type": desc.get("metric_type", "N/A"),
                        "params": desc.get("params", {}),
                    }

                    # Try to get index build progress
                    try:
                        progress = client.get_index_build_progress(
                            collection_name=collection,
                            index_name=idx_name,
                        )
                        if progress:
                            index_info["build_progress"] = progress
                    except Exception:
                        pass

                    result["indexes"].append(index_info)
                except Exception as e:
                    result["indexes"].append({
                        "index_name": idx_name,
                        "error": str(e),
                    })

            return json.dumps(result, ensure_ascii=False, indent=2, default=str)

        except Exception as e:
            return f"获取集合 '{collection}' 的索引信息失败: {str(e)}"

    def _get_indexes_for_all_collections(self, client) -> str:
        """Get index info for all collections."""
        collections = client.list_collections()

        if not collections:
            return "当前数据库中没有集合 / No collections in the current database"

        result = {
            "total_collections": len(collections),
            "collections": [],
        }

        for coll_name in collections:
            try:
                index_names = client.list_indexes(coll_name)
                indexes = []
                for idx_name in index_names:
                    try:
                        desc = client.describe_index(coll_name, idx_name)
                        indexes.append({
                            "index_name": idx_name,
                            "field_name": desc.get("field_name", "N/A"),
                            "index_type": desc.get("index_type", "N/A"),
                            "metric_type": desc.get("metric_type", "N/A"),
                            "params": desc.get("params", {}),
                        })
                    except Exception:
                        indexes.append({"index_name": idx_name})

                result["collections"].append({
                    "name": coll_name,
                    "index_count": len(index_names),
                    "indexes": indexes,
                })
            except Exception as e:
                result["collections"].append({
                    "name": coll_name,
                    "error": str(e),
                })

        return json.dumps(result, ensure_ascii=False, indent=2, default=str)
