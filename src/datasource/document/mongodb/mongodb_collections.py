"""MongoDB collection listing handler.

Lists collections in a MongoDB database, optionally filtered by name pattern.
"""

from typing import Optional

from connection.pool_manager import MultiDBPoolManager
from config.dbconfig import get_db_config_by_name


class MongoDBCollections:
    """List collections in a MongoDB database."""

    def get_collection_names(
        self,
        pool_name: str,
        pattern: Optional[str] = None,
    ) -> str:
        """List collections in the database.

        Args:
            pool_name: Connection pool name.
            pattern: Optional name pattern filter (regex-like, case-insensitive).

        Returns:
            Formatted collection list string.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        config = get_db_config_by_name(pool_name)
        db_name = config.get("database", "admin")

        with pool.connection() as client:
            db = client[db_name]

            try:
                collections = list(db.list_collections())

                if not collections:
                    return f"数据库 '{db_name}' 中没有集合"

                # Filter by pattern
                if pattern:
                    import re
                    try:
                        regex = re.compile(pattern, re.IGNORECASE)
                        collections = [
                            c for c in collections
                            if regex.search(c.get("name", ""))
                        ]
                    except re.error:
                        # If pattern is not a valid regex, do simple contains match
                        collections = [
                            c for c in collections
                            if pattern.lower() in c.get("name", "").lower()
                        ]

                if not collections:
                    return f"没有匹配 '{pattern}' 的集合"

                lines = [f"=== 数据库 '{db_name}' 中的集合 ({len(collections)} 个) ==="]
                for coll in collections:
                    name = coll.get("name", "N/A")
                    coll_type = coll.get("type", "collection")
                    options = coll.get("options", {})
                    lines.append(f"  - {name} (type: {coll_type})")

                    # Include additional info if available
                    if options:
                        for opt_key, opt_val in options.items():
                            lines.append(f"      {opt_key}: {opt_val}")

                return "\n".join(lines)

            except Exception as e:
                return f"获取集合列表失败: {str(e)}"
