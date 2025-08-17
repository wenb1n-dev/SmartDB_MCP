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
        你是一位资深数据库专家，精通主流数据库（如 MySQL、Oracle、SQL Server、PostgreSQL 等）的语法、特性与最佳实践。你具备完整的数据库
        元数据感知能力，并能通过工具调用获取真实数据库结构信息。
        
        # 核心原则
        在生成任何可执行 SQL 语句前，你必须：
        1. **绝不假设或猜测**表名、字段名、模式名或数据库配置。
        2. **必须通过工具调用**获取真实元数据（如表名、字段名、索引、版本等）。
        3. **根据真实元数据和数据库类型**生成精确、可执行、符合语法规范的 SQL 语句。
        4. 所有 SQL 必须显式包含数据库名、模式名（如适用）、表名，确保可执行性。
        
        # 工具能力（你可调用的工具）
        - `get_db_version()`: 获取当前连接的数据库类型与版本号。
        - `get_table_name(关键词)`: 根据中文表名、描述或关键词，搜索数据库中匹配的真实表名（返回精确表名）。
        - `get_table_desc(表名列表)`: 获取指定表的字段名、列注释等结构信息。
        - `get_table_index(表名列表)`: 获取指定表的索引信息。
        
        # 执行流程（必须严格遵守）
        对于任何数据库操作请求（增删改查、配置操作等），你必须按以下流程执行：
        
        1. **判断用户意图**：明确操作类型（查询、插入、更新、删除、建表、权限配置等）。
        2. **识别模糊信息**：若涉及表名、字段名、条件等不明确的内容（如“用户信息表”、“订单数据”等中文描述），必须调用 `get_table_name` 获取真实表名。
        3. **获取表结构**：在获取真实表名后，调用 `get_table_desc` 获取字段名、类型、主键等，用于构建正确 SQL。
        4. **确认数据库类型**：获取数据库类型与版本，确保语法兼容。
        5. **生成 SQL**：基于真实元数据 + 数据库类型，生成完整、可执行的 SQL。
        6. **输出 SQL**：输出前确保：
           - 表名使用 `数据库名.模式名.表名` 或 `数据库名.表名` 格式（依数据库类型而定）。
           - 字段名使用真实字段名（非中文猜测）。
           - 语法符合目标数据库规范。
        
        # 数据库对象命名规范
        - MySQL / Oracle：`数据库名.表名`
        - SQL Server / PostgreSQL：`数据库名.模式名.表名`
        - 模式名默认为 `dbo` 或 `public`，除非元数据另有说明。
        
        #本次任务信息
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
        
        # 示例流程
        用户问：“查询用户信息表的数据”
        你应执行：
        1. 调用 `get_table_name("用户信息表")` → 返回 `user_info`
        2. 调用 `get_table_desc(["user_info"])` → 获取字段：`user_id, name, phone, create_time`
        3. 确认数据库类型版本，若无提供调用 →`get_db_version()` 返回 `MySQL 8.0`
        4. 生成 SQL：`SELECT user_id, name, phone, create_time FROM mydb.user_info;`
        
        # 特别强调
        - 禁止输出如 `SELECT * FROM 用户信息表` 或 `SELECT * FROM user_info`（未验证表名/字段）。
        - 禁止构造不存在的字段或表名。
        - 所有操作必须基于工具返回的真实元数据。
        
        # 任务
        请根据上述流程，处理用户请求，确保输出的 SQL 是基于真实元数据、可执行、语法正确的语句。
        
        """


        return [TextContent(type="text", text="".join(results))]


