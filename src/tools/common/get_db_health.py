from typing import Dict, Sequence, Any, List

from mcp.types import TextContent, Tool

from config.dbconfig import get_db_config_by_name
from core.exceptions import SQLExecutionError
from datasource.registry import FactoryRegistry
from datasource.base import Paradigm
from tools.base import ToolsBase


class GetDbHealthTool(ToolsBase):
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

            # 通过多态调用获取范式专属诊断提示
            prompt = handler.get_prompt(results, db_version, db_type)

            return [TextContent(type="text", text=prompt)]

        except SQLExecutionError as e:
            return [TextContent(type="text", text=f"数据库执行错误: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"执行过程中发生错误: {str(e)}")]
