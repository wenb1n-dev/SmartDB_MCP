from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from databases.database_factory import DatabaseOperationFactory
from tools.base import ToolsBase

class GetTableIndex(ToolsBase):
    """数据库表索引查询工具类
    
    该类用于查询指定数据库表的索引信息。
    继承自ToolsBase基类，实现了获取工具描述和执行工具的核心方法。
    """
    
    # 工具名称
    name = "get_table_index"
    # 工具描述，包含中英文说明
    description = (
        "根据表名搜索数据库中对应的表索引,支持多表查询(Search for table indexes in the database based on table names, supporting multi-table queries)"
    )

    def get_tool_description(self) -> Tool:
        """获取工具的详细描述信息
        
        返回一个Tool对象，包含工具名称、描述和输入参数模式。
        该描述用于MCP服务识别和调用工具。
        
        Returns:
            Tool: 包含工具描述信息的对象
        """
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "tables": {
                        "type": "string",
                        "description": "要搜索表索引情况的表名，支持多个表名，用逗号分隔"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "数据库连接池名称，默认为default"
                    },
                    "database": {
                        "type": "string",
                        "description": "数据库名称,若无指定默认为default"
                    },
                    "schema": {
                        "type": "string",
                        "description": "数据库模式名称,若无指定默认为default"
                    }
                },
                "required": ["tables"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """执行表索引查询工具
        
        根据传入的参数查询指定表的索引信息。
        
        Args:
            arguments: 包含执行参数的字典
                - tables (str): 要查询索引的表名，支持多个表名用逗号分隔
                - pool_name (str, optional): 数据库连接池名称，默认为"default"
                - database (str, optional): 数据库名称，默认为"default"
                - schema (str, optional): 数据库模式名称，默认为"default"

        Returns:
            Sequence[TextContent]: 包含查询结果的文本内容序列
            
        Raises:
            ValueError: 当缺少必需的tables参数时抛出
            Exception: 当执行查询过程中出现其他错误时抛出
        """

        try:
            # 检查参数中是否包含必需的tables字段
            if "tables" not in arguments:
                raise ValueError("缺少查询语句")

            # 获取要查询索引的表名
            text = arguments["tables"]

            # 获取连接池名称，默认为"default"
            pool_name = arguments.get("pool_name", "default")

            # 获取数据库名称，默认为"default"
            database = arguments.get("database", "default")

            # 如果数据库名称为"default"，则设置为None
            database = database if database != "default" else None

            # 获取数据库模式名称，默认为"default"
            schema = arguments.get("schema", "default")
            # 如果模式名称为"default"，则设置为None
            schema = schema if schema != "default" else None

            # 根据连接池名称获取对应的数据库工厂实例
            factory = DatabaseOperationFactory.get_factory_by_pool_name(pool_name)

            # 创建表索引查询处理器实例
            handler = factory.create_table_index()

            # 执行表索引查询操作
            sql_result = handler.get_table_index(pool_name,database, schema, text)

            # 将查询结果转换为文本内容并返回
            return [TextContent(type="text", text=sql_result)]

        # 捕获执行过程中的异常并返回错误信息
        except Exception as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]