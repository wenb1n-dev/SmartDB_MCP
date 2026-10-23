"""MongoDB query execution handler.

Executes MongoDB queries (find, aggregate) with permission checking.
Supports find operations with filter, projection, sort, limit, skip,
and aggregate pipelines.
"""

import json
from typing import Any, Dict, List, Optional

from bson import json_util

from connection.pool_manager import MultiDBPoolManager
from config.dbconfig import get_db_config_by_name
from datasource.base import Paradigm
from permission.enforcer import enforcer


class MongoDBQueryExecutor:
    """Execute MongoDB queries with permission enforcement."""

    def execute_query(
        self,
        pool_name: str,
        collection: str,
        operation: str = "find",
        filter_doc: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        limit: int = 100,
        skip: int = 0,
        pipeline: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Execute a MongoDB query.

        Args:
            pool_name: Connection pool name.
            collection: Collection name.
            operation: Query operation - "find" or "aggregate".
            filter_doc: Filter document for find operations.
            projection: Projection document (field selection).
            sort: Sort specification list (e.g., [{"field": 1}]).
            limit: Maximum number of results (default: 100).
            skip: Number of documents to skip.
            pipeline: Aggregation pipeline for aggregate operations.

        Returns:
            JSON-formatted result string.
        """
        # 统一鉴权入口：FIND/AGGREGATE 均按目标执行池鉴权
        enforcer.authorize_category(
            pool_name,
            operation.upper(),
            Paradigm.DOCUMENT,
            tool="execute_mongo_query",
        ).raise_if_denied()

        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        config = get_db_config_by_name(pool_name)
        db_name = config.get("database", "admin")

        with pool.connection() as client:
            db = client[db_name]
            coll = db[collection]

            try:
                if operation.lower() == "find":
                    cursor = coll.find(
                        filter_doc or {},
                        projection=projection,
                    )
                    if sort:
                        cursor = cursor.sort(sort)
                    cursor = cursor.skip(skip).limit(limit)
                    results = list(cursor)
                    return self._format_results("find", collection, results)

                elif operation.lower() == "aggregate":
                    if not pipeline:
                        return "错误: aggregate 操作需要提供 pipeline 参数"
                    if limit:
                        pipeline = list(pipeline) + [{"$limit": limit}]
                    if skip:
                        pipeline = list(pipeline) + [{"$skip": skip}] if not limit else [{"$skip": skip}] + list(pipeline) + [{"$limit": limit}]
                    cursor = coll.aggregate(pipeline)
                    results = list(cursor)
                    return self._format_results("aggregate", collection, results)

                else:
                    return f"错误: 不支持的操作 '{operation}'，支持的操作: find, aggregate"

            except Exception as e:
                return f"查询执行失败: {str(e)}"

    def _format_results(self, operation: str, collection: str, results: List[Any]) -> str:
        """Format query results to a readable JSON string.

        Uses bson.json_util to handle ObjectId, datetime, etc.
        """
        if not results:
            return f"{operation} '{collection}' -> (空结果集)"

        # Use bson json_util to serialize MongoDB-specific types
        json_str = json.dumps(results, default=json_util.default, ensure_ascii=False, indent=2)

        lines = [
            f"{operation} '{collection}' -> ({len(results)} 条记录)",
            json_str,
        ]
        return "\n".join(lines)
