"""MongoDB index information handler.

Lists indexes on a MongoDB collection with key specifications and options.
"""

import json
from typing import Optional

from bson import json_util

from connection.pool_manager import MultiDBPoolManager
from config.dbconfig import get_db_config_by_name


class MongoDBIndexes:
    """Query index information for MongoDB collections."""

    def get_collection_indexes(
        self,
        pool_name: str,
        collection: Optional[str] = None,
    ) -> str:
        """Get index information for one or all collections.

        Args:
            pool_name: Connection pool name.
            collection: Collection name. If None, lists indexes for all collections.

        Returns:
            Formatted index information string.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        config = get_db_config_by_name(pool_name)
        db_name = config.get("database", "admin")

        with pool.connection() as client:
            db = client[db_name]

            try:
                if collection:
                    return self._get_indexes_for_collection(db, collection)
                else:
                    # List indexes for all collections
                    collections = list(db.list_collections())
                    if not collections:
                        return f"数据库 '{db_name}' 中没有集合"

                    sections = []
                    for coll_info in collections:
                        coll_name = coll_info["name"]
                        section = self._get_indexes_for_collection(db, coll_name)
                        sections.append(section)

                    return "\n\n".join(sections)

            except Exception as e:
                return f"获取索引信息失败: {str(e)}"

    def _get_indexes_for_collection(self, db, collection_name: str) -> str:
        """Get index info for a single collection."""
        try:
            coll = db[collection_name]
            indexes = list(coll.list_indexes())

            lines = [f"=== 集合 '{collection_name}' 的索引 ({len(indexes)} 个) ==="]

            for idx in indexes:
                idx_name = idx.get("name", "N/A")
                keys = idx.get("key", {})
                key_str = ", ".join(f"{k}: {v}" for k, v in keys.items())

                lines.append(f"\n  索引名: {idx_name}")
                lines.append(f"  键: {key_str}")

                # Additional index options
                if idx.get("unique"):
                    lines.append("  unique: true")
                if idx.get("sparse"):
                    lines.append("  sparse: true")
                if idx.get("partialFilterExpression"):
                    pfe = json.dumps(
                        idx["partialFilterExpression"],
                        default=json_util.default,
                        ensure_ascii=False,
                    )
                    lines.append(f"  partialFilterExpression: {pfe}")
                if idx.get("expireAfterSeconds") is not None:
                    lines.append(f"  TTL: {idx['expireAfterSeconds']}s")
                if idx.get("weights"):
                    lines.append(f"  weights: {idx['weights']}")

                version = idx.get("v", "N/A")
                lines.append(f"  version: {version}")

            return "\n".join(lines)

        except Exception as e:
            return f"=== 集合 '{collection_name}' ===\n获取索引失败: {str(e)}"
