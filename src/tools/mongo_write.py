"""MongoDB write execution MCP tool.

Allows MCP clients to execute MongoDB write operations
(insert/update/replace/delete) with permission enforcement.
Supports MongoDB Extended JSON ($oid/$date) inside documents/filters.
"""

from typing import Any, Dict, List, Optional, Sequence

from mcp.types import TextContent, Tool

from datasource.base import Paradigm
from datasource.registry import FactoryRegistry
from tools.base import ToolsBase


class ExecuteMongoWriteTool(ToolsBase):
    """MongoDB 写入执行工具

    执行 MongoDB 写操作（insert/update/replace/delete），带权限校验。
    仅适用于文档范式数据源；readonly 角色会被拒绝。
    """

    name = "execute_mongo_write"
    applicable_paradigms = [Paradigm.DOCUMENT]
    description = (
        "执行 MongoDB 写操作：insert_one/insert_many/update_one/update_many/"
        "replace_one/delete_one/delete_many。"
        "文档与过滤条件支持 MongoDB 扩展 JSON（如 {\"_id\": {\"$oid\": \"...\"}}）。"
        "【安全约束】update_many/delete_many 必须显式传入 filter（即使是空 {}），"
        "以防漏传导致全集合误改/误删；调用后必须立即结束，等待执行结果。"
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
                        "description": "集合名称 / Collection name",
                    },
                    "operation": {
                        "type": "string",
                        "enum": [
                            "insert_one",
                            "insert_many",
                            "update_one",
                            "update_many",
                            "replace_one",
                            "delete_one",
                            "delete_many",
                        ],
                        "description": "写操作类型 / Write operation type",
                    },
                    "document": {
                        "type": "object",
                        "description": "单文档（insert_one / replace_one）",
                    },
                    "documents": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "文档数组（insert_many）",
                    },
                    "filter": {
                        "type": "object",
                        "description": (
                            "过滤条件（update_*/delete_*/replace_one）；"
                            "update_many/delete_many 必须显式提供，空条件传 {}"
                        ),
                    },
                    "update": {
                        "type": "object",
                        "description": "更新表达式，须含 $set/$inc 等更新操作符（update_*）",
                    },
                    "replacement": {
                        "type": "object",
                        "description": "替换文档，不含更新操作符（replace_one）",
                    },
                    "upsert": {
                        "type": "boolean",
                        "description": "未命中时是否插入，默认 false",
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "连接池名称，默认为 default",
                    },
                },
                "required": ["collection", "operation"],
            },
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """执行 MongoDB 写操作。

        Args:
            arguments: 包含写入参数的字典，键与 executor.execute_write 对齐。

        Returns:
            Sequence[TextContent]: JSON 格式的写入结果。
        """
        try:
            if "collection" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 collection 参数")]
            if "operation" not in arguments:
                return [TextContent(type="text", text="错误: 缺少 operation 参数")]

            pool_name: str = arguments.get("pool_name", "default")
            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            executor = factory.create_write_executor()

            result = executor.execute_write(
                pool_name=pool_name,
                collection=arguments["collection"],
                operation=arguments["operation"],
                document=arguments.get("document"),
                documents=arguments.get("documents"),
                filter_doc=arguments.get("filter"),
                update=arguments.get("update"),
                replacement=arguments.get("replacement"),
                upsert=arguments.get("upsert", False),
            )

            # 写操作终点信号：阻止小模型拿到结果后继续重复调用写入工具
            result += (
                "\n\n[写入结束] 以上为最终写入结果，请勿再次调用 execute_mongo_write，"
                "直接向用户汇报结果。"
            )
            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"执行写入时出错: {str(e)}")]
