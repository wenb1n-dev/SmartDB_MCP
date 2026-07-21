"""Milvus vector search handler.

Performs similarity search on Milvus vector collections. Supports
different distance metrics, filter expressions, and output fields.
"""

import json
from typing import Any, Dict, List, Optional

from connection.pool_manager import MultiDBPoolManager


class MilvusVectorSearch:
    """Execute vector similarity search on Milvus collections."""

    def search(
        self,
        pool_name: str,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        output_fields: Optional[List[str]] = None,
        filter_expr: Optional[str] = None,
        search_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Perform a vector similarity search.

        Args:
            pool_name: Connection pool name.
            collection: Collection name.
            query_vector: Query vector (list of floats).
            top_k: Number of nearest neighbors to return (default: 10).
            output_fields: Fields to include in results. If None, returns
                          all fields except the vector field.
            filter_expr: Filter expression (e.g., 'id > 100').
            search_params: Search parameters dict (e.g., {"metric_type": "L2",
                          "params": {"ef": 64}}).

        Returns:
            JSON-formatted search results.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        with pool.connection() as client:
            try:
                # Default search params
                if search_params is None:
                    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

                # Default output fields
                if output_fields is None:
                    output_fields = ["*"]

                # Execute search using MilvusClient
                results = client.search(
                    collection_name=collection,
                    data=[query_vector],
                    limit=top_k,
                    filter=filter_expr or "",
                    output_fields=output_fields,
                    search_params=search_params,
                )

                # Format results
                return self._format_results(collection, query_vector, results)

            except Exception as e:
                return f"向量搜索失败: {str(e)}"

    def _format_results(
        self,
        collection: str,
        query_vector: List[float],
        results: Any,
    ) -> str:
        """Format search results to a readable JSON string."""
        vector_dim = len(query_vector)

        if not results:
            return f"向量搜索 '{collection}' (dim={vector_dim}) -> (空结果)"

        # MilvusClient.search returns a list of lists (one per query vector)
        # Since we only pass one query vector, results[0] has the matches
        if isinstance(results, list) and len(results) > 0:
            matches = results[0] if isinstance(results[0], list) else results
        else:
            matches = results

        formatted = {
            "collection": collection,
            "query_vector_dim": vector_dim,
            "total_matches": len(matches) if isinstance(matches, list) else 1,
            "results": [],
        }

        if isinstance(matches, list):
            for i, match in enumerate(matches):
                entry = {
                    "rank": i + 1,
                    "distance": match.get("distance", "N/A"),
                    "entity": match.get("entity", {}),
                }
                formatted["results"].append(entry)
        else:
            formatted["results"].append(matches)

        return json.dumps(formatted, ensure_ascii=False, indent=2, default=str)
