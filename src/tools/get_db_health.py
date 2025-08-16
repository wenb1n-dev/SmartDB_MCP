from typing import Dict, Sequence, Any, List

from mcp.types import TextContent, Tool

from config.dbconfig import get_db_config_by_name
from core.exceptions import SQLExecutionError
from databases.database_factory import DatabaseOperationFactory
from tools.base import ToolsBase


class DatabaseHealth(ToolsBase):
    """数据库健康检查工具"""

    name = "get_db_health"
    description = "获取当前的数据库健康状态"

    def get_tool_description(self) -> Tool:
        """获取工具描述"""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "health_type": {
                        "type": "string",
                        "description": ("检测类型，全部：all，索引健康分析：index，连接情况分析：connection，"
                                         "InnoDB 状态、事务、锁信息状态分析：blocking，资源情况分析：resources"
                                        "若没有指定默认是all")
                    },
                    "pool_name": {
                        "type": "string",
                        "description": "线程池名称,若没有指定默认是default"
                    }
                },
                "required": ["pool_name"]
            }
        )


    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """执行数据库健康检查工具

        Args:
            arguments: 包含检查参数的字典

        Returns:
            执行结果文本序列
        """
        if "pool_name" not in arguments:
            return [TextContent(type="text", text="错误: 缺少线程池名称")]

        pool_name = arguments["pool_name"]
        health_type = arguments.get("health_type", "all")

        try:
            # 获取数据库配置
            db_config = get_db_config_by_name(pool_name)
            # 获取数据库版本号
            factory = DatabaseOperationFactory.get_factory_by_pool_name(pool_name)
            db_version = factory.create_db_version().get_db_version(pool_name)

            factory = DatabaseOperationFactory.get_factory_by_pool_name(pool_name)

            handler = factory.create_db_health()
            results = handler.get_db_health(pool_name, health_type)

            prompt = f"""
            # 角色
            你是一位精通各大主流数据库的专家，拥有超过15年的数据库问题分析处理经验,负责根据给定的数据库类型
            分析数据库的健康问题。
            你具备跨平台诊断能力，熟悉各大主流数据库的：
            - 内部运行机制（锁、事务、日志、缓存）
            - 性能监控视图与命令（如 performance_schema、pg_stat、v$session、DMVs 等）
            - 常见性能瓶颈与调优策略
            - 安全、连接、死锁、长事务、索引失效等问题的识别与修复
            
            # 背景
            - 数据库类型
            {db_config["type"]}
            
            - 数据库版本号
            {db_version}
            
            {results}
            
            # 任务
            - 仔细评估提供的数据库情况信息，并提供诊断报告和解决方案。
            
            # 分析要求（结构化输出）
            ## 数据库健康状态诊断报告
            ----- 
            ### 1.【数据库类型、版本信息】
            
            ### 2.【整体健康评估】
            - 判断当前是否存在严重问题（死锁、阻塞、连接耗尽、高延迟等）
            - 给出健康等级：🟢 健康 / 🟡 警告 / 🔴 严重】
            
            ### 3. 【分项诊断】
            按以下维度分析（仅输出存在的数据,若无提供对应的数据库情况信息，则需提示未提供分析的数据，无法进行分析，不要自己自行构造或推测）：
            - **连接问题**：连接数、失败连接、空闲连接过多等
            - **事务问题**：长事务、未提交事务、事务隔离级别
            - **锁与阻塞**：锁等待、死锁、表锁/行锁争用
            - **资源使用**：缓冲池命中率、临时表使用、磁盘 I/O、死元组、事务 ID 年龄、SGA内存、PGA内存使用情况等，根据数据返回的内容进行扩展分析
            
            ### 4. 【根因分析】
            结合数据库行为推断根本原因，例如：
            - 应用未提交事务
            - 缺少索引导致扫描
            - 配置不合理（如 max_connections、work_mem）
            - 锁粒度粗（如表锁替代行锁）
            
            ### 5. 【解决方案建议】
            提供**数据库类型专属**的可执行建议，格式：
            - ✅ **优化建议**：如“为 large_table 添加复合索引”
            - 💡 **SQL/命令示例**：使用对应数据库语法
            - ⚙️ **配置建议**：如 `work_mem = 64MB`（PG）、`innodb_buffer_pool_size`（MySQL）
            - 📊 **监控建议**：建议开启慢查询、设置告警
            
            ### 6. 【风险提示】
            - 标注操作风险等级（低/中/高）
            - 提示生产环境需备份、评估影响
            
            ## 输出要求
            - 使用清晰的 Markdown 结构
            - 所有建议必须基于输入数据，避免臆测
            - 若信息不足，请明确指出：“需补充以下信息：...”
            - 对于 SQLite 等轻量数据库，说明其监控局限性

            """

            return [TextContent(type="text", text=prompt)]

        except SQLExecutionError as e:
            return [TextContent(type="text", text=f"数据库执行错误: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"执行过程中发生错误: {str(e)}")]