"""工具层统一权限 Guard。

在 MCP 工具真正调用数据源处理器之前，先基于工具声明的 PermissionSpec 完成鉴权，
保证「鉴权池 == 执行池」。数据源层仍保留 enforcer 校验作为纵深防御。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set

from datasource.base import Paradigm
from permission.enforcer import enforcer
from permission.operations import SQLOperation


# 操作解析器：从工具入参提取操作键；SQL 工具返回 SQLOperation 集合
CategoryOperationResolver = Callable[[Dict[str, Any]], List[str]]
SqlOperationResolver = Callable[[Dict[str, Any]], Set[SQLOperation]]


@dataclass(frozen=True)
class PermissionSpec:
    """单个 MCP 工具的权限声明。

    Attributes:
        paradigm: 目标数据源范式；通用元数据工具按实际连接池动态解析。
        category_resolver: 非关系型工具的操作键解析器。
        sql_resolver: 关系型工具的 SQL 操作集合解析器。
        pool_arg: 工具入参中的连接池参数名。
        default_pool: 未显式传入 pool_name 时使用的默认池。
        dynamic_paradigm: 是否根据目标池类型动态确定范式（通用工具）。
    """

    paradigm: Optional[Paradigm] = None
    category_resolver: Optional[CategoryOperationResolver] = None
    sql_resolver: Optional[SqlOperationResolver] = None
    pool_arg: str = "pool_name"
    default_pool: str = "default"
    dynamic_paradigm: bool = False

    def resolve_pool_name(self, arguments: Dict[str, Any]) -> str:
        """从工具入参中解析连接池名称。"""
        from connection.pool_resolver import pool_resolver

        explicit_pool_name = arguments.get(self.pool_arg)
        if explicit_pool_name is None and self.default_pool != "default":
            explicit_pool_name = self.default_pool
        return pool_resolver.resolve(explicit_pool_name)


def fixed_category_operation(operation: str) -> CategoryOperationResolver:
    """创建固定分类操作的解析器。"""
    def resolve(_: Dict[str, Any]) -> List[str]:
        return [operation]

    return resolve


def redis_command_operations(arguments: Dict[str, Any]) -> List[str]:
    """从 Redis 命令文本中提取首关键字。"""
    command = str(arguments.get("command") or "").strip().split()
    return [command[0].upper()] if command else ["UNKNOWN"]


def mongo_query_operations(arguments: Dict[str, Any]) -> List[str]:
    """解析 MongoDB 查询工具操作。"""
    return [str(arguments.get("operation") or "find").upper()]


def mongo_write_operations(arguments: Dict[str, Any]) -> List[str]:
    """解析 MongoDB 写入工具操作，并让未知写入键 fail-closed 到 ADMIN。"""
    from datasource.document.mongodb.mongodb_writer import MONGO_WRITE_OPERATIONS

    operation = str(arguments.get("operation") or "").strip().lower()
    return [MONGO_WRITE_OPERATIONS.get(operation, "ADMIN")]


def es_query_operations(arguments: Dict[str, Any]) -> List[str]:
    """解析 Elasticsearch 查询工具操作。"""
    return [str(arguments.get("operation") or "search").upper()]


def kafka_consumer_lag_operations(arguments: Dict[str, Any]) -> List[str]:
    """解析 Kafka 消费者组延迟工具操作。"""
    return ["DESCRIBE_GROUP" if arguments.get("group_id") else "LIST_GROUPS"]


def sql_query_operations(arguments: Dict[str, Any]) -> Set[SQLOperation]:
    """从关系型工具的 query/sql 入参提取 SQL 操作集合。"""
    from utils.execute_sql_util import ExecuteSqlUtil

    sql = str(arguments.get("query") or arguments.get("sql") or arguments.get("text") or "")
    operations = ExecuteSqlUtil.extract_operations(sql)
    return operations or {SQLOperation.OTHER}


def metadata_sql_operations(_: Dict[str, Any]) -> Set[SQLOperation]:
    """元数据/诊断类关系型工具只需要只读权限。"""
    return {SQLOperation.SELECT}


class PermissionGuard:
    """根据 PermissionSpec 在工具层执行统一鉴权。"""

    def authorize(self, tool_name: str, spec: PermissionSpec, arguments: Dict[str, Any]):
        """执行鉴权并返回 AuthDecision。

        通用工具不预先绑定范式：根据目标池的工厂范式选择 SQL 或分类鉴权。
        """
        pool_name = spec.resolve_pool_name(arguments)

        if spec.dynamic_paradigm:
            return self._authorize_dynamic(tool_name, pool_name, arguments)

        if spec.sql_resolver is not None:
            return enforcer.authorize_sql(
                pool_name,
                spec.sql_resolver(arguments),
                tool=tool_name,
            )

        if spec.category_resolver is not None and spec.paradigm is not None:
            operations = spec.category_resolver(arguments)
            decision = None
            for operation in operations:
                decision = enforcer.authorize_category(
                    pool_name,
                    operation,
                    spec.paradigm,
                    tool=tool_name,
                )
                if not decision.allowed:
                    return decision
            return decision

        # 工具未声明权限时 fail-closed，避免新增工具裸奔
        return enforcer.authorize_category(
            pool_name,
            "ADMIN",
            Paradigm.DOCUMENT,
            tool=tool_name,
        )

    @staticmethod
    def _authorize_dynamic(tool_name: str, pool_name: str, arguments: Dict[str, Any]):
        """通用工具按目标池实际范式鉴权，关系型元数据工具按 SELECT 处理。"""
        from config.dbconfig import get_db_config_by_name
        from datasource.registry import FactoryRegistry

        config = get_db_config_by_name(pool_name)
        factory_class = FactoryRegistry._factory_classes.get(config.get("type"))
        if factory_class is None:
            return enforcer.authorize_category(
                pool_name,
                "ADMIN",
                Paradigm.DOCUMENT,
                tool=tool_name,
            )

        paradigm = factory_class.paradigm
        if paradigm == Paradigm.RELATIONAL:
            return enforcer.authorize_sql(
                pool_name,
                metadata_sql_operations(arguments),
                tool=tool_name,
            )

        return enforcer.authorize_category(
            pool_name,
            "READ",
            paradigm,
            tool=tool_name,
        )


permission_guard = PermissionGuard()
