"""运行期权限鉴权的唯一入口（纵深防御的第二层）。

所有 datasource 执行器与工具层 Guard 都应通过 :class:`PermissionEnforcer` 鉴权，
不再直接 ``new XxxPolicy().check_permissions(...)``，从而保证：

1. 鉴权所用 ``pool_name`` 与最终执行所用的池【严格一致】；
2. 池不存在、角色非法、操作未授权等一切不确定情形一律 fail-closed；
3. 每次决策都有结构化审计日志。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, List, Set

from config.dbconfig import get_db_config_by_name
from core.exceptions import ConfigurationError, DataSourcePermissionError
from permission.audit import log_authz_decision
from permission.base import CategoryBasedPermissionPolicy, SqlPermissionPolicy
from permission.operations import SQLOperation
from permission.es_permission import ESPermissionPolicy
from permission.kafka_permission import KafkaPermissionPolicy
from permission.milvus_permission import MilvusPermissionPolicy
from permission.mongo_permission import MongoPermissionPolicy
from permission.redis_permission import RedisPermissionPolicy
from permission.roles import Role

if TYPE_CHECKING:
    from datasource.base import Paradigm


# 范式值 -> 对应分类策略（关系型走独立的 SqlPermissionPolicy）
# 这里使用字符串值，避免 permission.enforcer -> datasource 包初始化 -> 具体处理器 -> enforcer 的循环导入
_PARADIGM_POLICIES = {
    "kv_store": RedisPermissionPolicy,
    "document": MongoPermissionPolicy,
    "vector": MilvusPermissionPolicy,
    "search_engine": ESPermissionPolicy,
    "message_queue": KafkaPermissionPolicy,
}


@dataclass
class AuthDecision:
    """单次鉴权决策结果。"""

    allowed: bool
    pool_name: str
    role: str = ""
    requested: List[str] = field(default_factory=list)
    reason: str = ""

    def raise_if_denied(self) -> None:
        if not self.allowed:
            raise DataSourcePermissionError(self.reason)


class PermissionEnforcer:
    """无状态的统一鉴权器（角色实时读取配置结果，不做进程内缓存）。"""

    def __init__(self):
        self._sql_policy = SqlPermissionPolicy()
        self._category_policies = {
            paradigm_value: policy_cls()
            for paradigm_value, policy_cls in _PARADIGM_POLICIES.items()
        }

    # ------------------------------------------------------------------
    # 内部：解析角色（池缺失 / 角色非法均 fail-closed）
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_role(pool_name: str) -> Role:
        config = get_db_config_by_name(pool_name)  # 池缺失抛 ValueError
        return Role.parse(config.get("role"), pool_name=pool_name)

    # ------------------------------------------------------------------
    # 关系型：SQL 操作集合
    # ------------------------------------------------------------------
    def authorize_sql(
        self,
        pool_name: str,
        operations: Set[SQLOperation],
        *,
        tool: str = "",
    ) -> AuthDecision:
        """对一组 SQL 操作鉴权。空集合按 fail-closed 拒绝。"""
        requested = sorted(op.value for op in operations)
        try:
            if not operations:
                # 理论上 extract_operations 已保证非空，这里做双保险
                raise DataSourcePermissionError(
                    "权限不足: 未能识别语句操作类型，按安全策略默认拒绝"
                )
            self._sql_policy.check_permissions(pool_name, operations)
            role = self._resolve_role(pool_name)
            decision = AuthDecision(True, pool_name, role.value, requested)
        except (DataSourcePermissionError, ConfigurationError, ValueError) as exc:
            role = self._safe_role(pool_name)
            decision = AuthDecision(False, pool_name, role, requested, str(exc))

        log_authz_decision(
            allowed=decision.allowed,
            pool_name=pool_name,
            role=decision.role,
            tool=tool,
            paradigm="relational",
            operations=requested,
            reason=decision.reason,
        )
        return decision

    # ------------------------------------------------------------------
    # 非关系型：单个操作分类键
    # ------------------------------------------------------------------
    def authorize_category(
        self,
        pool_name: str,
        operation_key: str,
        paradigm: "Paradigm",
        *,
        tool: str = "",
    ) -> AuthDecision:
        """对一个分类化操作（如 INSERTONE / SEARCH / SET）鉴权。"""
        key = (operation_key or "").upper().strip()
        paradigm_value = paradigm.value
        requested = [key]
        try:
            if paradigm_value == "relational":
                raise ConfigurationError("关系型鉴权请使用 authorize_sql")
            policy = self._category_policies.get(paradigm_value)
            if policy is None:
                raise ConfigurationError(f"未知范式，无权限策略: {paradigm_value}")
            policy.check_permissions(pool_name, key)
            role = self._resolve_role(pool_name)
            decision = AuthDecision(True, pool_name, role.value, requested)
        except (DataSourcePermissionError, ConfigurationError, ValueError) as exc:
            role = self._safe_role(pool_name)
            decision = AuthDecision(False, pool_name, role, requested, str(exc))

        log_authz_decision(
            allowed=decision.allowed,
            pool_name=pool_name,
            role=decision.role,
            tool=tool,
            paradigm=paradigm_value,
            operations=requested,
            reason=decision.reason,
        )
        return decision

    @staticmethod
    def _safe_role(pool_name: str) -> str:
        """决策被拒后尽力读取角色用于审计，读不到则返回空串。"""
        try:
            return PermissionEnforcer._resolve_role(pool_name).value
        except Exception:
            return ""


# 进程级单例
enforcer = PermissionEnforcer()
