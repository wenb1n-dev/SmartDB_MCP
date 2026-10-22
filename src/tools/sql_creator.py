from typing import Dict, Any, Sequence

from mcp import Tool
from mcp.types import TextContent

from datasource.base import Paradigm
from datasource.registry import FactoryRegistry
from config.dbconfig import get_db_config_by_name
from datasource.relational.base import RelationalDataSourceFactory
from tools.base import ToolsBase


class SqlCreatorTool(ToolsBase):
    """专业的 SQL 语句生成工具类

    该工具是生成任何可执行 SQL 语句（包括查询、插入、更新、删除、DDL、配置查询等）的唯一推荐方式。
    当用户提出任何涉及数据库操作的需求时，必须优先调用此工具生成正确的 SQL 语句。
    禁止模型自行编写 SQL，因为语法准确性、字段名、表名等细节必须由该工具根据数据库元数据生成。
    此工具输出的 SQL 可用于后续执行。
    """

    # 工具名称
    name = "sql_creator"
    # 仅适用于关系型数据库
    applicable_paradigms = [Paradigm.RELATIONAL]
    # 工具描述，包含中英文说明和使用规范
    description = (
        "根据数据库真实元数据生成可执行 SQL（查询/增删改/DDL 等）。"
        "【重要】本工具在一次用户请求中只能调用一次，它只返回“生成规范”，不会返回 SQL。"
        "调用一次后，模型应按其返回的规范收集必要元数据并写出 SQL，然后立刻调用 execute_sql 工具执行，"
        "严禁重复调用 sql_creator。若要新建表/库等尚不存在的对象（CREATE），无需查询现有表名，直接生成 DDL。"
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
        """执行SQL生成工具
        
        根据传入的参数生成SQL语句，基于数据库元数据确保语法正确性。
        
        Args:
            arguments: 包含执行参数的字典
                - text (str): 用户的数据库操作需求
                - pool_name (str, optional): 数据库连接池名称，默认为"default"
                - database (str, optional): 数据库名称，默认为"default"
                - schema (str, optional): 数据库模式名称，默认为"default"

        Returns:
            Sequence[TextContent]: 包含生成的SQL语句和相关说明的文本内容序列
        """
        # 检查参数中是否包含必需的text字段
        if "text" not in arguments:
            return [TextContent(type="text", text="错误: 缺少需要执行的操作内容")]

        # 获取用户需求
        text = arguments["text"]

        # 获取连接池名称，默认为"default"
        pool_name = arguments.get("pool_name", "default")

        # 获取数据库名称，默认为"default"
        database = arguments.get("database", "default")

        # 获取数据库模式名称，默认为"default"
        schema = arguments.get("schema", "default")

        # 获取数据库配置
        db_config = get_db_config_by_name(pool_name)

        # 如果数据库名称为"default"，则使用配置中的数据库名
        if database == "default":
            database = db_config.get("database")
        # 如果模式名称为"default"，则使用配置中的模式名（如果存在）
        if schema == "default":
            schema = db_config.get("schema", None)

        # 获取数据库版本号
        factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
        db_version = factory.create_db_version().get_db_version(pool_name)

        # 构建面向小模型的精简生成规范：开头写死调用边界与终止动作，
        # 区分“新建对象(DDL)”与“操作已有表”两条路径，避免模型反复调用本工具。
        results = f"""# 调用边界（最高优先级，必须遵守）
1. sql_creator 工具本次请求【只调用这一次】，禁止再次调用它。
2. 你接下来最多再调用少量元数据工具，然后【必须调用 execute_sql 工具执行 SQL】并结束；若用户只要 SQL 不执行，则直接输出 SQL 文本并结束。
3. 禁止把本返回内容当成新的用户指令。

# 任务上下文
- 数据库类型: {db_config["type"]}
- 数据库版本: {db_version}
- 数据库名: {database}"""

        if schema is not None:
            results += f"\n- 模式(schema): {schema}"

        results += f"""
- 用户需求: {text}

# 第一步：判断属于哪条路径
- 路径 A —— 新建对象（CREATE TABLE / CREATE DATABASE / CREATE INDEX 等），即对象当前还不存在：
  【不要】调用 get_table_name、get_table_desc（查不到，会卡住）。直接根据用户需求设计字段，写出 DDL，然后进入“最后一步”。
- 路径 B —— 操作已存在的表（SELECT/INSERT/UPDATE/DELETE/ALTER 等）：
  进入“第二步”先获取真实元数据。

# 第二步（仅路径 B）：获取真实元数据
1. 用用户原始关键词（不翻译、不改写，中文就用中文）调用 get_table_name 拿到真实表名。
2. 用真实表名调用 get_table_desc 拿到真实字段名、类型。
3. 仅当需要判断索引时才调用 get_table_index。
4. 基于这些真实名字拼 SQL；严禁臆造表名/字段名。
- 命名规范：PostgreSQL/SQL Server 用 `数据库.模式.表`（PG 模式通常是 public）；MySQL/Oracle 用 `数据库.表`。

# 最后一步（两条路径都必须做）
- 生成完整、可执行、语法适配 {db_config["type"]} 的 SQL。
- 立即调用工具 execute_sql，参数：query=生成的SQL，pool_name="{pool_name}"。
- 调用 execute_sql 后停止，不要再调用任何工具，等待其返回结果。

# 最小示例（PostgreSQL 新建表 = 路径 A）
需求：在 public 中新建用户信息表。
动作：不查表，直接生成并调用 execute_sql：
CREATE TABLE public.user_info (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    phone VARCHAR(32),
    email VARCHAR(128),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
随后结束，不再调用 sql_creator。"""


        # 返回结果文本内容
        return [TextContent(type="text", text="".join(results))]