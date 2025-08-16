from typing import Dict, Any, Sequence

from mcp import Tool
from mcp.types import TextContent

from config.dbconfig import get_db_config_by_name
from databases.database_factory import DatabaseOperationFactory
from tools.base import ToolsBase


class SqlCreator(ToolsBase):
    name = "sql_creator"
    description = ("专业的 SQL 语句生成工具。该工具是生成任何可执行 SQL 语句（包括查询、插入、更新、删除、DDL、配置查询等）的唯一推荐方式。"
                   "当用户提出任何涉及数据库操作的需求时，必须优先调用此工具生成正确的 SQL 语句。"
                   "禁止模型自行编写 SQL，因为语法准确性、字段名、表名等细节必须由该工具根据数据库元数据生成。"
                   "此工具输出的 SQL 可用于后续执行。")

    def get_tool_description(self) -> Tool:
        """获取工具描述"""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "用户需求"
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
        """执行SQL工具

                Args:
                    arguments: 包含SQL查询的参数字典

                Returns:
                    执行结果文本序列
                """
        if "text" not in arguments:
            return [TextContent(type="text", text="错误: 缺少需要执行的操作内容")]

        text = arguments["text"]

        pool_name = arguments.get("pool_name", "default")

        database = arguments.get("database", "default")

        schema = arguments.get("schema", "default")

        # 获取数据库配置
        db_config = get_db_config_by_name(pool_name)

        # 获取数据库模式，pg

        if database == "default":
            database = db_config.get("database")
        if schema == "default":
            schema = db_config.get("schema", None)

        # 获取数据库版本号
        factory = DatabaseOperationFactory.get_factory_by_pool_name(pool_name)
        db_version = factory.create_db_version().get_db_version(pool_name)

        results = f"""
        #角色
        你是一位数据库专家，精通各大主流的数据库。你的任务是根据提供的数据库类型和SQL操作类型，编写适配该数据库的执行SQL语句。
        
        #背景
        - 数据库类型与版本号:
        {db_config["type"]}
        {db_version}
        
        - 所需连接的数据库名：
        {database}
            
      """
        if schema is not None:
            results += f"- 数据库模式：{schema}\n"

        results += f"""
        - SQL操作内容（增删改查、数据库配置查询语句、操作语句等）:
        {text}
        
        #要求
        在编写SQL语句时，请遵循以下指南:
        1. 确保SQL语句与指定的数据库类型相适配，考虑不同数据库在语法和功能上的差异。
        2. 对于增删改查操作，要明确操作的表名、字段名等必要信息，编写完整且正确的语句。
        3. 对于数据库配置的查询和操作语句，要准确针对该数据库类型的配置项进行编写。
        4. 语句要简洁、清晰，避免不必要的复杂性。
        
        #任务
        - 根据数据库类型与版本号、所需连接的数据库名、连接的模式、操作要求编写可执行的SQL语句。
        - 注意生成的SQL语句要正确、完整、可执行，且要满足数据库类型与版本号的要求。
        - 注意生成的SQL语句要指定数据库名、模式名，避免执行错误。例如Oracle，mysql数据库，要指定数据库名.表名。sqlserver，pg数据库，要指定数据库名.模式名.表名。
        - 调用工具执行SQL语句。
        
        """


        return [TextContent(type="text", text="".join(results))]


