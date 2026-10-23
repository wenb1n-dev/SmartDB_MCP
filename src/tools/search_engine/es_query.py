"""Elasticsearch DSL query MCP tool.

Allows MCP clients to execute Elasticsearch DSL queries (search, count, aggregate).
"""

import json
from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from datasource.registry import FactoryRegistry
from tools.base import ToolsBase


class ExecuteESQueryTool(ToolsBase):
    """Elasticsearch DSL 查询工具

    执行 Elasticsearch DSL 查询（search/count/aggregate），支持全功能 DSL。
    仅适用于搜索引擎范式数据源。
    """

    name = "execute_es_query"
    applicable_paradigms = [Paradigm.SEARCH_ENGINE]
    description = (
        "执行 Elasticsearch DSL 查询（search/count/aggregate），支持全功能 DSL。"
        "Execute Elasticsearch DSL queries (search/count/aggregate) with full DSL support."
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "index": {
                        "type": "string",
                        "description": "索引名称（可用逗号分隔多个索引或使用通配符）/ Index name (comma-separated or wildcard)"
                    },
                    "query_body": {
                        "type": "object",
                        "description": "DSL 查询体（完整的查询 JSON）/ DSL query body (full query JSON)"
                    },
                    "operation": {
                        "type": "string",
                        "enum": ["search", "count", "aggregate"],
                        "description": "查询操作类型，默认 search / Query operation type, default: search"
                    },
                    "size": {
                        "type": "integer",
                        "description": "返回结果数量限制（仅 search），默认 100 / Result limit (search only), default: 100"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "连接池名称，默认为 default / Connection pool name, default: default"
                    }
                },
                "required": ["index", "query_body"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute an Elasticsearch DSL query.

        Args:
            arguments: Dictionary containing query parameters.

        Returns:
            Sequence[TextContent]: Query result.
        """
        try:
            if "index" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 index 参数")]
            if "query_body" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 query_body 参数")]

            index = arguments["index"]
            query_body = arguments["query_body"]
            operation = arguments.get("operation", "search")
            size = arguments.get("size", 100)
            pool_name = arguments.get("pool_name", "default")

            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            executor = factory.create_query_executor()

            result = executor.execute_query(
                pool_name=pool_name,
                index=index,
                query_body=query_body,
                operation=operation,
                size=size,
            )

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"执行 ES 查询时出错: {str(e)}")]
