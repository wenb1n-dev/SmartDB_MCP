"""Permission policy abstraction layer.

Defines the PermissionPolicy ABC and SqlPermissionPolicy implementation.
Each data source paradigm can implement its own permission policy while
maintaining a unified interface for permission checking.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Set
from enum import Enum

from config.dbconfig import get_db_config_by_name, get_role_permissions


class PermissionPolicy(ABC):
    """Abstract base class for permission policies.

    Each data source paradigm should implement its own permission policy
    that defines how roles map to allowed operations.
    """

    @abstractmethod
    def get_role(self, pool_name: str) -> str:
        """Get the role configured for a specific connection pool.

        Args:
            pool_name: The connection pool name.

        Returns:
            The role string (e.g., "readonly", "writer", "admin").
        """
        ...

    @abstractmethod
    def get_allowed_operations(self, role: str) -> List[str]:
        """Get the list of allowed operations for a role.

        Args:
            role: The role name.

        Returns:
            List of allowed operation identifiers.
        """
        ...

    @abstractmethod
    def check_permissions(self, pool_name: str, operations: Any) -> bool:
        """Check if the pool's role allows the given operations.

        Args:
            pool_name: The connection pool name.
            operations: The operations to check (type depends on paradigm).

        Returns:
            True if all operations are allowed.

        Raises:
            Exception: When permissions are insufficient.
        """
        ...


class SQLOperation(str, Enum):
    """SQL operation type enumeration."""
    SELECT = 'SELECT'
    INSERT = 'INSERT'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    CREATE = 'CREATE'
    ALTER = 'ALTER'
    DROP = 'DROP'
    TRUNCATE = 'TRUNCATE'
    SHOW = 'SHOW'
    DESCRIBE = 'DESCRIBE'
    EXPLAIN = 'EXPLAIN'

    @classmethod
    def from_str(cls, value: str) -> 'SQLOperation':
        """Create SQLOperation from string.

        Args:
            value: SQL operation string.

        Returns:
            SQLOperation: Corresponding enum value.

        Raises:
            ValueError: When operation type is not supported.
        """
        try:
            return cls(value.upper())
        except ValueError:
            raise ValueError(f"不支持的SQL操作类型: {value}")


class SqlPermissionPolicy(PermissionPolicy):
    """Permission policy for relational databases.

    Maps the readonly/writer/admin roles to allowed SQL operation types.
    """

    def get_role(self, pool_name: str) -> str:
        """Get the role for a specific pool."""
        config = get_db_config_by_name(pool_name)
        return config.get("role", "readonly")

    def get_allowed_operations(self, role: str) -> List[str]:
        """Get allowed SQL operations for a role."""
        return get_role_permissions(role)

    def check_permissions(self, pool_name: str, operations: Set[SQLOperation]) -> bool:
        """Check if the pool's role allows the given SQL operations.

        Args:
            pool_name: The connection pool name.
            operations: Set of SQLOperation to check.

        Returns:
            True if all operations are allowed.

        Raises:
            SQLPermissionError: When permissions are insufficient.
        """
        from core.exceptions import SQLPermissionError

        role = self.get_role(pool_name)
        allowed = {SQLOperation.from_str(op) for op in self.get_allowed_operations(role)}
        unauthorized = operations - allowed

        if unauthorized:
            raise SQLPermissionError(
                f"权限不足: 当前角色无权执行以下操作: {', '.join(op.value for op in unauthorized)}"
            )
        return True
