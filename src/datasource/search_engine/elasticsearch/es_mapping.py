"""Elasticsearch index mapping handler.

Queries index mappings (field types, analyzers, settings).
"""

import json
from typing import Optional

from connection.pool_manager import MultiDBPoolManager


class ElasticsearchMapping:
    """Query index mappings for Elasticsearch indices."""

    def get_index_mapping(
        self,
        pool_name: str,
        index: str,
    ) -> str:
        """Get index mapping (field types, analyzers).

        Args:
            pool_name: Connection pool name.
            index: Index name (or comma-separated list).

        Returns:
            JSON-formatted mapping information.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        with pool.connection() as client:
            try:
                mapping = client.indices.get_mapping(index=index)

                # Also get settings for each index
                try:
                    settings = client.indices.get_settings(index=index)
                except Exception:
                    settings = {}

                result = {
                    "indices": {},
                }

                for idx_name, idx_data in mapping.items():
                    idx_mapping = idx_data.get("mappings", {})
                    idx_settings = settings.get(idx_name, {}).get("settings", {}).get("index", {})

                    # Extract key settings
                    settings_summary = {
                        "number_of_shards": idx_settings.get("number_of_shards", "N/A"),
                        "number_of_replicas": idx_settings.get("number_of_replicas", "N/A"),
                    }

                    # Count fields
                    properties = idx_mapping.get("properties", {})
                    field_count = len(properties)

                    result["indices"][idx_name] = {
                        "mappings": idx_mapping,
                        "settings": settings_summary,
                        "field_count": field_count,
                    }

                return json.dumps(result, ensure_ascii=False, indent=2, default=str)

            except Exception as e:
                return f"获取索引 mapping 失败: {str(e)}"
