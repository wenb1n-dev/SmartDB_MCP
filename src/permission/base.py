"""Permission policy abstraction layer.

Defines the PermissionPolicy ABC, CategoryBasedPermissionPolicy base class,
and SqlPermissionPolicy implementation.

- PermissionPolicy: ABC for all paradigms.
- CategoryBasedPermissionPolicy: Base for non-relational paradigms that use
  a 4-category (READ/WRITE/ADMIN/DANGEROUS) classification model.
- SqlPermissionPolicy: Relational permission policy using SQLOperation enums.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Set
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
            DataSourcePermissionError: When permissions are insufficient.
        """
        ...


class OperationCategory(str, Enum):
    """Generic 4-value operation category used by non-relational paradigms."""
    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"
    DANGEROUS = "DANGEROUS"


class CategoryBasedPermissionPolicy(PermissionPolicy):
    """Base class for category-based permission policies.

    Non-relational paradigms (Redis, MongoDB, Milvus, ES, Kafka) all follow
    the same pattern: operations are classified into READ/WRITE/ADMIN/DANGEROUS
    categories, and roles map to allowed category sets.

    Subclasses must provide:
        - ``_OPERATION_CATEGORIES``: Dict mapping operation strings to
          ``OperationCategory`` values.
        - ``_DANGEROUS_COMMANDS``: Set of operation strings that are dangerous.
        - ``_datasource_name``: String for error messages (e.g. "Redis").
    """

    _OPERATION_CATEGORIES: Dict[str, OperationCategory] = {}
    _DANGEROUS_COMMANDS: Set[str] = set()
    _datasource_name: str = ""

    _ROLE_CATEGORIES: Dict[str, Set[OperationCategory]] = {
        "readonly": {OperationCategory.READ},
        "writer": {OperationCategory.READ, OperationCategory.WRITE},
        "admin": {
            OperationCategory.READ,
            OperationCategory.WRITE,
            OperationCategory.ADMIN,
            OperationCategory.DANGEROUS,
        },
    }

    def get_role(self, pool_name: str) -> str:
        """Get the role configured for a specific pool."""
        config = get_db_config_by_name(pool_name)
        return config.get("role", "readonly")

    def get_allowed_operations(self, role: str) -> Set[OperationCategory]:
        """Get allowed operation categories for a role."""
        return self._ROLE_CATEGORIES.get(role, self._ROLE_CATEGORIES["readonly"])

    def check_permissions(self, pool_name: str, operation: str) -> bool:
        """Check if the pool's role allows the given operation.

        Args:
            pool_name: The connection pool name.
            operation: The operation string (e.g., ``"GET"``, ``"SEARCH"``).

        Returns:
            True if the operation is allowed.

        Raises:
            DataSourcePermissionError: When permissions are insufficient.
        """
        from core.exceptions import DataSourcePermissionError

        operation_upper = operation.upper().strip()
        role = self.get_role(pool_name)
        allowed_categories = self.get_allowed_operations(role)
        category = self._get_operation_category(operation_upper)

        if category not in allowed_categories:
            raise DataSourcePermissionError(
                f"权限不足: 当前角色 '{role}' 无权执行 {self._datasource_name} "
                f"操作 '{operation_upper}' (分类: {category.value})"
            )

        return True

    def _get_operation_category(self, operation: str) -> OperationCategory:
        """Get the category for an operation.

        Falls back to ADMIN for unknown operations (conservative approach).
        """
        if operation in self._OPERATION_CATEGORIES:
            return self._OPERATION_CATEGORIES[operation]

        if operation in self._DANGEROUS_COMMANDS:
            return OperationCategory.DANGEROUS

        return OperationCategory.ADMIN


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
            DataSourcePermissionError: When permissions are insufficient.
        """
        from core.exceptions import DataSourcePermissionError

        role = self.get_role(pool_name)
        allowed = {SQLOperation.from_str(op) for op in self.get_allowed_operations(role)}
        unauthorized = operations - allowed

        if unauthorized:
            raise DataSourcePermissionError(
                f"权限不足: 当前角色无权执行以下操作: {', '.join(op.value for op in unauthorized)}"
            )
        return True
