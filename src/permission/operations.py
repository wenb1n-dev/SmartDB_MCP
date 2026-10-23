"""权限相关的操作分类与 SQL 操作枚举。

独立成模块是为了打破 ``permission.base``（策略基类）与
``permission.roles``（角色矩阵）之间的循环导入：二者都只依赖这里的枚举。
"""

from __future__ import annotations

from enum import Enum
from typing import Dict


# 关键字别名归一化（不同方言的同义写法）。定义在 Enum 类外，避免被 Enum 转换为成员。
_SQL_KEYWORD_ALIASES: Dict[str, str] = {
    'DESC': 'DESCRIBE',
    'EXEC': 'CALL',
    'EXECUTE': 'CALL',
}


class OperationCategory(str, Enum):
    """Generic 4-value operation category used by non-relational paradigms."""

    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"
    DANGEROUS = "DANGEROUS"


class SQLOperation(str, Enum):
    """SQL operation type enumeration.

    ``OTHER`` 是兜底分类：任何无法可靠识别的语句首关键字都映射到它，
    且没有任何内置角色默认拥有该权限（fail-closed），避免「识别不了就放行」。
    """

    # ---- 只读 ----
    SELECT = 'SELECT'
    SHOW = 'SHOW'
    DESCRIBE = 'DESCRIBE'
    EXPLAIN = 'EXPLAIN'
    # ---- 读写（writer 及以上）----
    INSERT = 'INSERT'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    MERGE = 'MERGE'
    REPLACE = 'REPLACE'
    # ---- 管理类 DDL / 会话（仅 admin）----
    CREATE = 'CREATE'
    ALTER = 'ALTER'
    DROP = 'DROP'
    TRUNCATE = 'TRUNCATE'
    GRANT = 'GRANT'
    REVOKE = 'REVOKE'
    CALL = 'CALL'
    DO = 'DO'
    LOAD = 'LOAD'
    COPY = 'COPY'
    LOCK = 'LOCK'
    RENAME = 'RENAME'
    SET = 'SET'
    USE = 'USE'
    # ---- 无法识别：默认拒绝 ----
    OTHER = 'OTHER'

    @classmethod
    def from_str(cls, value: str) -> 'SQLOperation':
        """Create SQLOperation from string.

        无法识别时【不抛异常】，而是返回兜底的 ``OTHER``，交由权限层默认拒绝。

        Args:
            value: SQL operation string.

        Returns:
            SQLOperation: Corresponding enum value, or ``OTHER``.
        """
        normalized = (value or "").strip().upper()
        normalized = _SQL_KEYWORD_ALIASES.get(normalized, normalized)
        try:
            return cls(normalized)
        except ValueError:
            return cls.OTHER
