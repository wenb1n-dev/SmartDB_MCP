from typing import Dict, Sequence, Any

from mcp.types import TextContent, Tool

from core.exceptions import SQLExecutionError
from databases.database_factory import DatabaseOperationFactory
from tools.base import ToolsBase


class DatabaseVersion(ToolsBase):
    """数据库版本查询工具类
    
    该类用于查询指定连接池所连接的数据库版本信息。
    继承自ToolsBase基类，实现了获取工具描述和执行工具的核心方法。
    """

    # 工具名称
    name = "get_db_version"
    # 工具描述
    description = "查询某个连接池连接的数据库版本号 / Query the database version number of a connection pool connection"


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
                    "pool_name": {
                        "type": "string",
                        "description": "连接池名称，用于指定要查询版本的数据库连接池"
                    }
                },
                "required": ["pool_name"]
            }
        )


    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """执行数据库版本查询工具
        
        根据传入的连接池名称，查询对应数据库的版本信息。
        
        Args:
            arguments: 包含执行参数的字典
                - pool_name (str): 要查询的数据库连接池名称

        Returns:
            Sequence[TextContent]: 包含查询结果的文本内容序列
            
        Raises:
            SQLExecutionError: 当SQL执行出现错误时抛出
        """
        # 检查参数中是否包含必需的pool_name字段
        if "pool_name" not in arguments:
            return [TextContent(type="text", text="错误: 缺少线程池名称")]

        # 获取连接池名称
        pool_name = arguments["pool_name"]

        try:
            # 根据连接池名称获取对应的数据库工厂实例
            factory = DatabaseOperationFactory.get_factory_by_pool_name(pool_name)

            # 创建数据库版本查询处理器实例
            handler = factory.create_db_version()

            # 执行数据库版本查询操作
            sql_results = handler.get_db_version(pool_name)

            # 将查询结果转换为文本内容并返回
            return [TextContent(type="text", text="".join(sql_results))]

        # 捕获SQL执行错误并返回错误信息
        except SQLExecutionError as e:
            return [TextContent(type="text", text=str(e))]