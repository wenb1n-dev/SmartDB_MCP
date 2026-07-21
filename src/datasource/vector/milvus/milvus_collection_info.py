"""Milvus collection info handler.

Queries collection metadata: name, dimension, distance metric, schema,
entity count, etc.
"""

import json
from typing import Optional

from connection.pool_manager import MultiDBPoolManager


class MilvusCollectionInfo:
    """Query collection information for Milvus vector collections."""

    def get_collection_info(
        self,
        pool_name: str,
        collection: Optional[str] = None,
    ) -> str:
        """Get collection information.

        Args:
            pool_name: Connection pool name.
            collection: Collection name. If None, lists all collections
                       with basic info.

        Returns:
            JSON-formatted collection information.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        with pool.connection() as client:
            try:
                if collection:
                    return self._get_single_collection_info(client, collection)
                else:
                    return self._get_all_collections_info(client)
            except Exception as e:
                return f"获取集合信息失败: {str(e)}"

    def _get_single_collection_info(self, client, collection: str) -> str:
        """Get detailed info for a single collection."""
        # Get collection description (schema)
        desc = client.describe_collection(collection)

        # Get collection stats
        try:
            stats = client.get_collection_stats(collection)
            row_count = stats.get("row_count", "N/A")
        except Exception:
            row_count = "N/A"

        # Get index info
        try:
            indexes = client.list_indexes(collection)
        except Exception:
            indexes = []

        # Parse schema
        fields = []
        schema_fields = desc.get("fields", [])
        for field in schema_fields:
            field_info = {
                "name": field.get("name", "N/A"),
                "type": field.get("type", "N/A"),
                "is_primary": field.get("is_primary", False),
                "auto_id": field.get("auto_id", False),
            }
            # Add params if available (e.g., dimension for vector fields)
            params = field.get("params", {})
            if params:
                field_info["params"] = params
            fields.append(field_info)

        info = {
            "collection_name": collection,
            "description": desc.get("description", ""),
            "auto_id": desc.get("auto_id", False),
            "enable_dynamic_field": desc.get("enable_dynamic_field", False),
            "fields": fields,
            "row_count": row_count,
            "index_count": len(indexes) if isinstance(indexes, list) else indexes,
            "indexes": indexes if isinstance(indexes, list) else [],
        }

        return json.dumps(info, ensure_ascii=False, indent=2, default=str)

    def _get_all_collections_info(self, client) -> str:
        """Get basic info for all collections."""
        collections = client.list_collections()

        if not collections:
            return "当前数据库中没有集合 / No collections in the current database"

        result = {
            "total_collections": len(collections),
            "collections": [],
        }

        for coll_name in collections:
            try:
                desc = client.describe_collection(coll_name)
                try:
                    stats = client.get_collection_stats(coll_name)
                    row_count = stats.get("row_count", "N/A")
                except Exception:
                    row_count = "N/A"

                # Extract vector dimension and metric type from fields
                vector_dim = None
                metric_type = None
                for field in desc.get("fields", []):
                    params = field.get("params", {})
                    if isinstance(params, dict):
                        if "dim" in params:
                            vector_dim = params["dim"]
                        if "metric_type" in params:
                            metric_type = params["metric_type"]

                result["collections"].append({
                    "name": coll_name,
                    "row_count": row_count,
                    "vector_dimension": vector_dim,
                    "metric_type": metric_type,
                    "fields": len(desc.get("fields", [])),
                })
            except Exception as e:
                result["collections"].append({
                    "name": coll_name,
                    "error": str(e),
                })

        return json.dumps(result, ensure_ascii=False, indent=2, default=str)
