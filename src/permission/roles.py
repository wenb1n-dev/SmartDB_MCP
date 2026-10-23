"""角色与权限矩阵的单一事实来源（single source of truth）。

历史上关系型角色表定义在 ``config/dbconfig.ROLE_PERMISSIONS``，非关系型角色表
定义在 ``permission/base.CategoryBasedPermissionPolicy._ROLE_CATEGORIES``，两份
事实来源容易漂移。本模块统一收口：

- :class:`Role`：三档角色枚举（非法角色 fail-closed，不再静默降级）。
- :data:`ROLE_SQL_OPERATIONS`：关系型 角色 -> 允许的 SQLOperation 集合。
- :data:`ROLE_CATEGORIES`：非关系型 角色 -> 允许的操作类别集合。

任何权限策略都只能从这里读取矩阵，禁止再散落第二份定义。
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Set

from core.exceptions import ConfigurationError
from permission.operations import OperationCategory, SQLOperation


class Role(str, Enum):
    """产品级三档角色。"""

    READONLY = "readonly"
    WRITER = "writer"
    ADMIN = "admin"

    @classmethod
    def parse(cls, value: str, pool_name: str = "") -> "Role":
        """把配置中的角色字符串解析为枚举，非法角色直接报错（fail-closed）。

        Args:
            value: 配置中的 role 值。
            pool_name: 连接池名，仅用于错误信息定位。

        Raises:
            ConfigurationError: 角色不是三档之一时。
        """
        try:
            return cls(str(value).strip().lower())
        except (ValueError, AttributeError):
            scope = f"连接池 '{pool_name}' " if pool_name else ""
            valid = ", ".join(r.value for r in cls)
            raise ConfigurationError(
                f"{scope}配置了非法角色 '{value}'，合法值为: {valid}"
            )


# ---- 关系型：角色 -> SQL 操作集合 -------------------------------------------------

ROLE_SQL_OPERATIONS: Dict[Role, Set[SQLOperation]] = {
    Role.READONLY: {
        SQLOperation.SELECT,
        SQLOperation.SHOW,
        SQLOperation.DESCRIBE,
        SQLOperation.EXPLAIN,
    },
    Role.WRITER: {
        SQLOperation.SELECT,
        SQLOperation.SHOW,
        SQLOperation.DESCRIBE,
        SQLOperation.EXPLAIN,
        SQLOperation.INSERT,
        SQLOperation.UPDATE,
        SQLOperation.DELETE,
        # MERGE/REPLACE 本质是写操作
        SQLOperation.MERGE,
        SQLOperation.REPLACE,
    },
    Role.ADMIN: {
        # 读写
        SQLOperation.SELECT,
        SQLOperation.SHOW,
        SQLOperation.DESCRIBE,
        SQLOperation.EXPLAIN,
        SQLOperation.INSERT,
        SQLOperation.UPDATE,
        SQLOperation.DELETE,
        SQLOperation.MERGE,
        SQLOperation.REPLACE,
        # DDL
        SQLOperation.CREATE,
        SQLOperation.ALTER,
        SQLOperation.DROP,
        SQLOperation.TRUNCATE,
        # 权限 / 例程 / 数据装载 / 会话（可能内含任意操作，仅 admin）
        SQLOperation.GRANT,
        SQLOperation.REVOKE,
        SQLOperation.CALL,
        SQLOperation.DO,
        SQLOperation.LOAD,
        SQLOperation.COPY,
        SQLOperation.LOCK,
        SQLOperation.RENAME,
        SQLOperation.SET,
        SQLOperation.USE,
    },
    # 注意：SQLOperation.OTHER 不授予任何角色 → 无法识别的语句默认拒绝
}

# ---- 非关系型：角色 -> 操作类别集合 ----------------------------------------------

ROLE_CATEGORIES: Dict[Role, Set[OperationCategory]] = {
    Role.READONLY: {OperationCategory.READ},
    Role.WRITER: {OperationCategory.READ, OperationCategory.WRITE},
    Role.ADMIN: {
        OperationCategory.READ,
        OperationCategory.WRITE,
        OperationCategory.ADMIN,
        OperationCategory.DANGEROUS,
    },
}

VALID_ROLES = tuple(r.value for r in Role)
