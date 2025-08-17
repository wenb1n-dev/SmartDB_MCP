from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from databases.database_factory import DatabaseOperationFactory
from tools.base import ToolsBase

class GetTableName(ToolsBase):
    """数据库表名查询工具类
    
    该类用于查询数据库中的所有表名或根据表的中文名称/描述搜索对应的表名。
    继承自ToolsBase基类，实现了获取工具描述和执行工具的核心方法。
    """
    
    # 工具名称
    name = "get_table_name"
    # 工具描述，包含中英文说明和使用场景说明
    description = (
        "数据库表名查询工具。用于查询数据库中的所有表名或将根据表的中文名称或表描述搜索数据库中对应的表名。"
        "当用户需要列出数据库中的所有表或者根据表的中文描述查找具体表名时使用此工具。"
        "Database table name query tool. Used to query all table names in the database or search for corresponding table names based on the description of the table."
        "Use this tool when the user needs to list all tables in a database or find the specific table name based on its description."
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
                    "text": {
                        "type": "string",
                        "description": "要搜索的表描述，搜索包含某个关键词的表名。若要查询所有表，请使用'SEARCH_ALL_TABLES'关键词"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "线程池名称,若没有指定默认是default"
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
                "required": ["text"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """执行表名查询工具
        
        根据传入的参数查询数据库中的表名信息。
        
        Args:
            arguments: 包含执行参数的字典
                - text (str): 要搜索的表描述关键词，使用'SEARCH_ALL_TABLES'可查询所有表
                - pool_name (str, optional): 数据库连接池名称，默认为"default"
                - database (str, optional): 数据库名称，默认为"default"
                - schema (str, optional): 数据库模式名称，默认为"default"

        Returns:
            Sequence[TextContent]: 包含查询结果的文本内容序列
            
        Raises:
            ValueError: 当缺少必需的text参数时抛出
            Exception: 当执行查询过程中出现其他错误时抛出
        """

        try:
            # 检查参数中是否包含必需的text字段
            if "text" not in arguments:
                raise ValueError("缺少查询语句")

            # 获取要搜索的表描述关键词
            text = arguments["text"]

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

            # 创建表名查询处理器实例
            handler = factory.create_table_name()

            # 执行表名查询操作
            sql_result = handler.get_table_name(pool_name,database, schema, text)

            # 将查询结果转换为文本内容并返回
            return [TextContent(type="text", text=sql_result)]

        # 捕获执行过程中的异常并返回错误信息
        except Exception as e:
            return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]