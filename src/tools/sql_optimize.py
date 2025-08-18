from typing import Dict, Any, Sequence

from mcp import Tool
from mcp.types import TextContent

from databases.database_factory import DatabaseOperationFactory
from tools.base import ToolsBase

class SqlOptimize(ToolsBase):

    # 工具名称
    name = "sql_optimize"
    # 工具描述，包含中英文说明和使用规范
    description = ("专业的SQL性能优化工具，基于MySQL执行计划、表结构信息、表数据量、表索引提供专家级优化建议。"
        "该工具能够分析SQL语句的执行效率，识别性能瓶颈，并提供具体的优化方案，"
        "包括索引优化、查询重写建议等，帮助提升数据库查询性能。"
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
                        "description": "需要优化的sql"
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "线程池名称,若没有指定默认是default"
                    },
                    "tables": {
                        "type": "string",
                        "description": "需要优化sql中的所有表，若sql含有数据库名，需要一同传入，例如数据库.表名，以,分割。"
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
            return [TextContent(type="text", text="错误: 缺少需要执行优化的sql内容")]

        if "tables" not in arguments:
            return [TextContent(type="text", text="错误: 缺少需要执行优化的sql的表信息")]

        # 获取用户需求
        text = arguments["text"]

        # 获取连接池名称，默认为"default"
        pool_name = arguments.get("pool_name", "default")

        tables_group = self._parse_tables(arguments.get("tables"))

        factory = DatabaseOperationFactory.get_factory_by_pool_name(pool_name)
        # 获取数据库版本
        db_version = factory.create_db_version().get_db_version(pool_name)

        # 获取表索引
        index_info:str = ""

        # 获取表结构
        table_desc_info:str = ""

        # 获取表大小
        table_size_info:str = ""

        for table_info in tables_group:
            index_info += factory.create_table_index().get_table_index(pool_name,table_info.get("database"),
                                                                        table_info.get("schema"), table_info.get("table_name")) + "\n"

            table_desc_info += factory.create_table_description().get_table_description(pool_name,table_info.get("database"),
                                                                        table_info.get("schema"), table_info.get("table_name")) + "\n"

            table_size_info += factory.create_sql_optimize().get_table_size(pool_name,table_info.get("database"),
                                                                            table_info.get("schema"), table_info.get("table_name")) + "\n"

        print(text)

        # 获取sql执行计划
        sql_explain = factory.create_sql_optimize().get_sql_explain(pool_name, text)

        result = f"""
                # 角色设定
                你是一位世界级的数据库性能优化专家，拥有超过15年SQL调优经验，擅长深度执行计划分析和索引优化。
                
                # 任务目标
                你将严格遵循以下 **五步分析法**，对用户提供的SQL进行专业级优化。**每一步必须输出明确结论，不得跳过或合并步骤**
                
                ## 第一步：信息确认与表结构分析
                请先确认以下信息是否完整：
                1. 数据库类型与版本
                {db_version}
                2. SQL语句
                {text}
                3. 相关表的结构（字段、类型、主键）
                {table_desc_info}
                4. 表的索引信息（名称、字段、类型）
                {index_info}
                5. 表的数据大小
                {table_size_info}
                6. 执行计划（EXPLAIN 或执行计划文本）
                {sql_explain}
                
                ## 第二步：执行计划深度解析
                请逐行分析执行计划，回答以下问题：
                1. 哪些操作是性能瓶颈？（如：Nested Loop、Hash Join、Sort、Seq Scan）
                2. 是否存在全表扫描？原因是什么？（如：缺少索引、索引未命中）
                3. 连接顺序是否合理？驱动表是否为小表？
                4. 是否存在不必要的排序或分组？
                5. 预估的行数与实际是否偏差大？是否导致错误的执行计划？
                
                输出格式：用表格列出关键步骤，标注“操作类型”、“成本”、“问题原因”。
                 
                ## 第三步：SQL逻辑问题诊断
                请检查以下常见问题，**每项必须明确“是/否”并说明理由**：
                - [ ] 是否使用了 `SELECT *`？应只查必要字段
                - [ ] WHERE 条件是否对字段使用了函数？（如 `WHERE YEAR(create_time) = 2024`）
                - [ ] 是否存在 `OR` 条件导致索引失效？
                - [ ] 是否使用 `IN (子查询)` 而未用 `EXISTS`？
                - [ ] 是否有隐式类型转换？（如字符串 vs 数字）
                - [ ] 是否使用 `DISTINCT` 或 `GROUP BY` 但无聚合需求？
                - [ ] 分页是否使用 `OFFSET` 过大？是否可用游标优化？
                - [ ] 是否存在多层嵌套子查询？可否用 CTE 或 JOIN 重写？
                
                输出格式：用 Markdown 表格列出问题项、是否存在问题、根本原因。
            
                ## 第四步：索引优化建议
                请基于前三步分析，提出索引优化方案：
                1. 现有索引是否被有效使用？未使用的索引建议删除。
                2. 是否需要创建复合索引？请给出**最优字段顺序**（区分度高在前）。
                3. 是否可使用**覆盖索引**避免回表？
                4. 对于大表分页，是否可使用“延迟关联”或“书签法”？
                
                输出格式：
                - 建议创建的索引（完整 DDL）
                - 建议删除的索引
                - 说明每个索引的作用和预期效果
 
                ## 第五步：优化SQL重写（仅限指定数据库）
                请提供 **1~2个优化版本的SQL**，必须满足：
                1. 严格基于 `<数据库类型与版本>` 的语法特性
                2. 使用覆盖索引、避免函数、优化连接顺序
                3. 如适用，提供“分页优化版”或“时间范围缩小版”
                4. 每个版本附带“预期性能提升”说明（如：从 10s → 200ms）
                
                输出格式：
                ```sql
                -- 优化版本1：使用覆盖索引 + EXISTS
                SELECT ...
                ```
                
                ## 第六步：实施建议与延伸思考
                实施建议
                - 实施步骤（如：先建索引 → 收集统计信息 → 测试）
                - 风险：长事务阻塞、锁表、空间占用
                - 验证方法：对比执行计划、响应时间、CPU/IO
                - 建议在低峰期执行
                
                延伸思考
                - 高并发下是否会出现锁争用？是否需要读写分离？
                - 数据量增长100倍后，当前方案是否仍有效？是否需分库分表？
                - 数据库参数建议（如：work_mem、effective_cache_size）
                - 此优化思路是否适用于其他相似查询？
                - 是否可考虑物化视图或缓存层？
                
                输出要求
                - 使用 Markdown 格式
                - 语言简洁、专业，避免空洞描述
                - 每一步必须输出，不得跳过
                - 不得提供其他数据库的优化建议
                
                最终输出结构如下：
                1. 表结构与索引分析
                2. 执行计划解析
                3. SQL逻辑问题诊断
                4. 索引优化建议
                5. 优化SQL重写
                6. 实施建议与延伸思考
                """

        # 返回结果文本内容
        return [TextContent(type="text", text="".join(result))]

    def _parse_tables(self, tables_str: str) -> list:
        """
        解析表名字符串，返回包含database、schema、tablename的字典列表

        Args:
            tables_str: 以逗号分隔的表名字符串

        Returns:
            包含表信息字典的列表，每个字典包含database、schema、tablename字段
        """
        if not tables_str:
            return []

        tables = tables_str.split(',')
        table_list = []

        for table in tables:
            table = table.strip()
            parts = table.split('.')
            table_info = {"database": "default", "schema": "default", "table_name": ""}

            if len(parts) == 1:
                # 只有表名，没有数据库或模式
                table_info["table_name"] = parts[0]

            elif len(parts) == 2:
                # 数据库.表名 格式
                table_info["database"] = parts[0]
                table_info["table_name"] = parts[1]

            elif len(parts) == 3:
                # 数据库.模式.表名 格式
                table_info["database"] = parts[0]
                table_info["schema"] = parts[1]
                table_info["table_name"] = parts[2]

            table_list.append(table_info)

        return table_list
