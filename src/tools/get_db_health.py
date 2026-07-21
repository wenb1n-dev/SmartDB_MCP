from typing import Dict, Sequence, Any, List

from mcp.types import TextContent, Tool

from config.dbconfig import get_db_config_by_name
from core.exceptions import SQLExecutionError
from databases.database_factory import FactoryRegistry
from datasource.base import Paradigm
from tools.base import ToolsBase


class DatabaseHealth(ToolsBase):
    """数据库健康检查工具

    支持所有范式的数据源（关系型/KV/文档等），通过工厂多态调用
    对应范式的健康检查处理器。
    """

    name = "get_db_health"
    description = "获取数据库健康状态 / Get database health status"

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
            db_type = db_config.get("type", "unknown")
            # 通过 FactoryRegistry 获取工厂（支持所有范式）
            factory = FactoryRegistry.get_factory_by_pool_name(pool_name)
            # 获取数据库版本号
            db_version = factory.create_db_version().get_db_version(pool_name)
            # 获取健康状态实例
            handler = factory.create_db_health()
            # 获取健康状态
            results = handler.get_db_health(pool_name, health_type)

            # 根据数据库类型生成不同的诊断提示
            if db_type == "redis":
                prompt = f"""
                # 角色
                你是一位精通 Redis 和各类内存数据库的专家，拥有超过 15 年的 Redis 运维和性能调优经验，
                负责根据给定的 Redis 健康数据进行分析和诊断。
                你熟悉：
                - Redis 内存管理与淘汰策略
                - 主从复制与哨兵/集群架构
                - 持久化机制（RDB/AOF）与性能影响
                - 慢查询分析与优化
                - 连接管理与客户端问题排查
                - 大 Key/热 Key 识别与处理

                # 背景
                - 数据库类型: Redis
                - 数据库版本号:
                {db_version}

                {results}

                # 任务
                - 仔细评估提供的 Redis 健康数据，提供诊断报告和解决方案。

                # 分析要求（结构化输出）
                ## Redis 健康状态诊断报告
                -----
                ### 1.【版本信息】

                ### 2.【整体健康评估】
                - 判断当前是否存在严重问题（内存溢出、连接耗尽、主从断开、慢查询堆积等）
                - 给出健康等级：🟢 健康 / 🟡 警告 / 🔴 严重

                ### 3. 【分项诊断】
                按以下维度分析（仅输出存在的数据，若无对应数据则提示未提供）：
                - **连接问题**：连接数、拒绝连接、阻塞客户端
                - **内存问题**：内存使用、碎片率、淘汰策略、OOM 风险
                - **持久化问题**：RDB/AOF 状态、保存耗时
                - **慢查询**：慢查询数量、耗时、命令类型
                - **复制状态**：主从连接、延迟、偏移量

                ### 4. 【根因分析】
                结合 Redis 行为推断根本原因，例如：
                - 大 Key 导致内存增长
                - 连接泄漏导致连接数耗尽
                - 持久化频率过高导致性能下降
                - 缺少过期策略导致内存膨胀

                ### 5. 【解决方案建议】
                提供 Redis 专属的可执行建议：
                - ✅ **优化建议**：如"拆分大 Key"、"设置合理过期时间"
                - 💡 **命令示例**：使用 Redis 语法
                - ⚙️ **配置建议**：如 `maxmemory-policy`、`save` 配置
                - 📊 **监控建议**：建议开启慢查询日志、设置告警

                ### 6. 【风险提示】
                - 标注操作风险等级（低/中/高）
                - 提示生产环境需备份、评估影响

                ## 输出要求
                - 使用清晰的 Markdown 结构
                - 所有建议必须基于输入数据，避免臆测
                - 若信息不足，请明确指出："需补充以下信息：..."
                """
            elif db_type == "mongodb":
                prompt = f"""
                # 角色
                你是一位精通 MongoDB 和各类文档数据库的专家，拥有超过 15 年的 MongoDB 运维和性能调优经验，
                负责根据给定的 MongoDB 健康数据进行分析和诊断。
                你熟悉：
                - MongoDB 存储引擎（WiredTiger）与内存管理
                - 副本集与分片集群架构
                - 索引优化与查询计划分析
                - 慢查询诊断与聚合管道优化
                - 连接池配置与并发控制
                - 数据建模与 Schema 设计

                # 背景
                - 数据库类型: MongoDB
                - 数据库版本号:
                {db_version}

                {results}

                # 任务
                - 仔细评估提供的 MongoDB 健康数据，提供诊断报告和解决方案。

                # 分析要求（结构化输出）
                ## MongoDB 健康状态诊断报告
                -----
                ### 1.【版本信息】

                ### 2.【整体健康评估】
                - 判断当前是否存在严重问题（内存溢出、连接耗尽、副本集异常、慢查询堆积等）
                - 给出健康等级：🟢 健康 / 🟡 警告 / 🔴 严重

                ### 3. 【分项诊断】
                按以下维度分析（仅输出存在的数据，若无对应数据则提示未提供）：
                - **连接问题**：连接数、可用连接、连接池配置
                - **内存与存储**：内存使用、存储大小、数据压缩比
                - **慢查询**：慢查询数量、运行时间、操作类型
                - **复制状态**：副本集状态、主从延迟、成员健康
                - **索引健康**：索引数量、冗余索引、未使用索引

                ### 4. 【根因分析】
                结合 MongoDB 行为推断根本原因，例如：
                - 缺少索引导致全表扫描
                - 文档过大导致内存压力
                - 聚合管道效率低下
                - 副本集延迟过大影响读一致性

                ### 5. 【解决方案建议】
                提供 MongoDB 专属的可执行建议：
                - ✅ **优化建议**：如"为查询字段添加复合索引"
                - 💡 **命令示例**：使用 MongoDB 语法
                - ⚙️ **配置建议**：如 `maxPoolSize`、`wiredTigerCacheSizeGB`
                - 📊 **监控建议**：建议开启 Profiler、设置告警

                ### 6. 【风险提示】
                - 标注操作风险等级（低/中/高）
                - 提示生产环境需备份、评估影响

                ## 输出要求
                - 使用清晰的 Markdown 结构
                - 所有建议必须基于输入数据，避免臆测
                - 若信息不足，请明确指出："需补充以下信息：..."
                """
            elif db_type == "milvus":
                prompt = f"""
                # 角色
                你是一位精通 Milvus 和各类向量数据库的专家，拥有超过 10 年的向量数据库运维和性能调优经验，
                负责根据给定的 Milvus 健康数据进行分析和诊断。
                你熟悉：
                - Milvus 架构（Proxy/QueryNode/DataNode/IndexNode）
                - 向量索引算法（HNSW/IVF/DISKANN/SCANN）
                - 距离度量（L2/IP/COSINE）与召回率优化
                - 分片与副本机制
                - 内存管理与磁盘换入换出
                - RAG 场景下的性能调优

                # 背景
                - 数据库类型: Milvus
                - 数据库版本号:
                {db_version}

                {results}

                # 任务
                - 仔细评估提供的 Milvus 健康数据，提供诊断报告和解决方案。

                # 分析要求（结构化输出）
                ## Milvus 健康状态诊断报告
                -----
                ### 1.【版本信息】

                ### 2.【整体健康评估】
                - 判断当前是否存在严重问题（节点宕机、索引构建失败、内存不足、查询超时等）
                - 给出健康等级：🟢 健康 / 🟡 警告 / 🔴 严重

                ### 3. 【分项诊断】
                按以下维度分析（仅输出存在的数据，若无对应数据则提示未提供）：
                - **连接与集合**：服务器版本、集合数量、实体总数
                - **内存与存储**：实体数量、存储大小、内存压力
                - **索引健康**：索引数量、索引类型、构建进度
                - **查询延迟**：搜索延迟、查询延迟
                - **节点状态**：副本组、节点数量、节点健康

                ### 4. 【根因分析】
                结合 Milvus 行为推断根本原因，例如：
                - 索引未构建导致全表扫描
                - nprobe 参数过低导致召回率不足
                - 集合未 load 到内存导致查询缓慢
                - 节点资源不足导致索引构建缓慢

                ### 5. 【解决方案建议】
                提供 Milvus 专属的可执行建议：
                - ✅ **优化建议**：如"为高频查询字段创建索引"
                - 💡 **命令示例**：使用 pymilvus 语法
                - ⚙️ **配置建议**：如 `nprobe`、`ef` 参数调优
                - 📊 **监控建议**：建议监控查询延迟、索引构建进度

                ### 6. 【风险提示】
                - 标注操作风险等级（低/中/高）
                - 提示生产环境需备份、评估影响

                ## 输出要求
                - 使用清晰的 Markdown 结构
                - 所有建议必须基于输入数据，避免臆测
                - 若信息不足，请明确指出："需补充以下信息：..."
                """
            else:
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
                - ✅ **优化建议**：如"为 large_table 添加复合索引"
                - 💡 **SQL/命令示例**：使用对应数据库语法
                - ⚙️ **配置建议**：如 `work_mem = 64MB`（PG）、`innodb_buffer_pool_size`（MySQL）
                - 📊 **监控建议**：建议开启慢查询、设置告警

                ### 6. 【风险提示】
                - 标注操作风险等级（低/中/高）
                - 提示生产环境需备份、评估影响

                ## 输出要求
                - 使用清晰的 Markdown 结构
                - 所有建议必须基于输入数据，避免臆测
                - 若信息不足，请明确指出："需补充以下信息：..."
                - 对于 SQLite 等轻量数据库，说明其监控局限性
                """

            return [TextContent(type="text", text=prompt)]

        except SQLExecutionError as e:
            return [TextContent(type="text", text=f"数据库执行错误: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"执行过程中发生错误: {str(e)}")]