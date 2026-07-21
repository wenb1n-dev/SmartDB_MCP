"""MongoDB execution plan MCP tool.

Runs ``explain`` on a MongoDB query to produce the execution plan.
"""

from typing import Dict, Sequence, Any, List

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from databases.database_factory import FactoryRegistry
from tools.base import ToolsBase


class MongoExplainTool(ToolsBase):
    """MongoDB 执行计划分析工具

    对 MongoDB 查询执行 explain，输出执行计划和统计信息。
    仅适用于文档范式数据源。
    """

    name = "mongo_explain"
    applicable_paradigms = [Paradigm.DOCUMENT]
    description = (
        "分析 MongoDB 查询的执行计划（explain），包括查询计划、执行统计、索引使用情况。"
        "Analyze MongoDB query execution plan (explain), including query planner, execution stats, index usage."
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
                    "pipeline": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "聚合管道（aggregate 操作） / Aggregation pipeline (for aggregate)"
                    },
                    "verbosity": {
                        "type": "string",
                        "enum": ["queryPlanner", "executionStats", "allPlansExecution"],
                        "description": "explain 详细程度，默认 allPlansExecution / Explain verbosity, default: allPlansExecution"
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
        """Run MongoDB explain.

        Args:
            arguments: Dictionary containing explain parameters.

        Returns:
            Sequence[TextContent]: Execution plan result.
        """
        try:
            if "collection" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 collection 参数")]

            collection = arguments["collection"]
            operation = arguments.get("operation", "find")
            filter_doc = arguments.get("filter", {})
            pipeline = arguments.get("pipeline")
            verbosity = arguments.get("verbosity", "allPlansExecution")
            pool_name = arguments.get("pool_name", "default")

            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            handler = factory.create_explain()

            result = handler.explain(
                pool_name=pool_name,
                collection=collection,
                operation=operation,
                filter_doc=filter_doc,
                pipeline=pipeline,
                verbosity=verbosity,
            )

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"执行计划分析时出错: {str(e)}")]
