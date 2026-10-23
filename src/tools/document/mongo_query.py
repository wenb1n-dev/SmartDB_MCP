"""MongoDB query execution MCP tool.

Allows MCP clients to execute MongoDB queries (find, aggregate) with
permission enforcement.
"""

import json
from typing import Dict, Sequence, Any, List

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from datasource.registry import FactoryRegistry
from tools.base import ToolsBase


class ExecuteMongoQueryTool(ToolsBase):
    """MongoDB 查询执行工具

    执行 MongoDB 查询（find/aggregate），带权限校验。
    仅适用于文档范式数据源。
    """

    name = "execute_mongo_query"
    applicable_paradigms = [Paradigm.DOCUMENT]
    description = (
        "执行 MongoDB 查询（find/aggregate），支持过滤、投影、排序、分页。"
        "Execute MongoDB queries (find/aggregate) with filter, projection, sort, pagination."
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
                    "operation": {
                        "type": "string",
                        "enum": ["find", "aggregate"],
                        "description": "查询操作类型，默认为 find / Query operation type, default: find"
                    },
                    "filter": {
                        "type": "object",
                        "description": "查询过滤条件（find 操作） / Query filter document (for find)"
                    },
                    "projection": {
                        "type": "object",
                        "description": "字段投影 / Field projection"
                    },
                    "sort": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "排序条件，如 [{\"field\": 1}] / Sort specification"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制，默认 100 / Result limit, default: 100"
                    },
                    "skip": {
                        "type": "integer",
                        "description": "跳过的文档数，默认 0 / Number of documents to skip"
                    },
                    "pipeline": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "聚合管道（aggregate 操作） / Aggregation pipeline (for aggregate)"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "连接池名称，默认为 default / Connection pool name, default: default"
                    }
                },
                "required": ["collection"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute a MongoDB query.

        Args:
            arguments: Dictionary containing query parameters.

        Returns:
            Sequence[TextContent]: Query result.
        """
        try:
            if "collection" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 collection 参数")]

            collection = arguments["collection"]
            operation = arguments.get("operation", "find")
            filter_doc = arguments.get("filter", {})
            projection = arguments.get("projection")
            sort = arguments.get("sort")
            limit = arguments.get("limit", 100)
            skip = arguments.get("skip", 0)
            pipeline = arguments.get("pipeline")
            pool_name = arguments.get("pool_name", "default")

            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            executor = factory.create_query_executor()

            result = executor.execute_query(
                pool_name=pool_name,
                collection=collection,
                operation=operation,
                filter_doc=filter_doc,
                projection=projection,
                sort=sort,
                limit=limit,
                skip=skip,
                pipeline=pipeline,
            )

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]
