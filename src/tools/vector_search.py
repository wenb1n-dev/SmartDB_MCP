"""Vector search MCP tool.

Allows MCP clients to perform vector similarity search on Milvus collections.
"""

import json
from typing import Dict, Sequence, Any, List

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from databases.database_factory import FactoryRegistry
from tools.base import ToolsBase


class VectorSearchTool(ToolsBase):
    """向量搜索工具

    在 Milvus 集合中执行向量相似度搜索，支持过滤表达式、距离度量、输出字段选择。
    仅适用于向量范式数据源。
    """

    name = "execute_vector_search"
    applicable_paradigms = [Paradigm.VECTOR]
    description = (
        "在向量集合中执行相似度搜索，返回最近的 K 个邻居。"
        "Execute vector similarity search on a collection, returning top-K nearest neighbors."
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "description": "集合名称 / Collection name"
                    },
                    "query_vector": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "查询向量（浮点数列表）/ Query vector (list of floats)"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回结果数量，默认 10 / Number of nearest neighbors to return, default: 10"
                    },
                    "output_fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "输出字段列表，默认返回所有字段 / Output fields, default: all fields"
                    },
                    "filter_expr": {
                        "type": "string",
                        "description": "过滤表达式（如 'id > 100'）/ Filter expression (e.g., 'id > 100')"
                    },
                    "search_params": {
                        "type": "object",
                        "description": "搜索参数（如 {\"metric_type\": \"L2\", \"params\": {\"nprobe\": 10}}）/ Search parameters"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "连接池名称，默认为 default / Connection pool name, default: default"
                    }
                },
                "required": ["collection", "query_vector"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute a vector similarity search.

        Args:
            arguments: Dictionary containing search parameters.

        Returns:
            Sequence[TextContent]: Search results.
        """
        try:
            if "collection" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 collection 参数")]
            if "query_vector" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 query_vector 参数")]

            collection = arguments["collection"]
            query_vector = arguments["query_vector"]
            top_k = arguments.get("top_k", 10)
            output_fields = arguments.get("output_fields")
            filter_expr = arguments.get("filter_expr")
            search_params = arguments.get("search_params")
            pool_name = arguments.get("pool_name", "default")

            # Permission check
            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            policy = factory.create_permission_policy()
            policy.check_permissions(pool_name, "SEARCH")

            handler = factory.create_vector_search()

            result = handler.search(
                pool_name=pool_name,
                collection=collection,
                query_vector=query_vector,
                top_k=top_k,
                output_fields=output_fields,
                filter_expr=filter_expr,
                search_params=search_params,
            )

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"向量搜索时出错: {str(e)}")]
