"""Elasticsearch DSL query handler.

Executes Elasticsearch DSL queries (search, count, aggregations) with
permission checking.
"""

import json
from typing import Any, Dict, Optional

from connection.pool_manager import MultiDBPoolManager
from datasource.base import Paradigm
from permission.enforcer import enforcer


class ElasticsearchQueryExecutor:
    """Execute Elasticsearch DSL queries with permission enforcement."""

    def execute_query(
        self,
        pool_name: str,
        index: str,
        query_body: Dict[str, Any],
        operation: str = "search",
        size: int = 100,
    ) -> str:
        """Execute an Elasticsearch DSL query.

        Args:
            pool_name: Connection pool name.
            index: Index name (or comma-separated list, or '_all').
            query_body: DSL query body (the full query JSON).
            operation: Query operation - "search", "count", or "aggregate".
            size: Maximum number of results for search (default: 100).

        Returns:
            JSON-formatted result string.
        """
        # 统一鉴权入口：SEARCH/COUNT/AGGREGATE 均按目标执行池鉴权
        enforcer.authorize_category(
            pool_name,
            operation.upper(),
            Paradigm.SEARCH_ENGINE,
            tool="execute_es_query",
        ).raise_if_denied()

        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        with pool.connection() as client:
            try:
                if operation.lower() == "search":
                    # Add size to the query body if not present
                    if "size" not in query_body:
                        query_body["size"] = size
                    result = client.search(index=index, body=query_body)

                    hits = result.get("hits", {})
                    total = hits.get("total", {})
                    total_value = total.get("value", 0) if isinstance(total, dict) else total
                    took_ms = result.get("took", 0)
                    timed_out = result.get("timed_out", False)

                    formatted = {
                        "index": index,
                        "operation": "search",
                        "took_ms": took_ms,
                        "timed_out": timed_out,
                        "total_hits": total_value,
                        "max_score": hits.get("max_score"),
                        "results": [],
                    }

                    for hit in hits.get("hits", []):
                        entry = {
                            "_id": hit.get("_id"),
                            "_score": hit.get("_score"),
                            "_source": hit.get("_source"),
                        }
                        if "highlight" in hit:
                            entry["highlight"] = hit["highlight"]
                        formatted["results"].append(entry)

                    # Include aggregations if present
                    if "aggregations" in result:
                        formatted["aggregations"] = result["aggregations"]

                    return json.dumps(formatted, ensure_ascii=False, indent=2, default=str)

                elif operation.lower() == "count":
                    result = client.count(index=index, body=query_body)
                    return json.dumps(result, ensure_ascii=False, indent=2, default=str)

                elif operation.lower() == "aggregate":
                    # Aggregation-only search (size=0)
                    query_body["size"] = 0
                    result = client.search(index=index, body=query_body)
                    aggs = result.get("aggregations", {})
                    took_ms = result.get("took", 0)
                    formatted = {
                        "index": index,
                        "operation": "aggregate",
                        "took_ms": took_ms,
                        "aggregations": aggs,
                    }
                    return json.dumps(formatted, ensure_ascii=False, indent=2, default=str)

                else:
                    return f"错误: 不支持的操作 '{operation}'，支持: search, count, aggregate"

            except Exception as e:
                return f"ES 查询执行失败: {str(e)}"
