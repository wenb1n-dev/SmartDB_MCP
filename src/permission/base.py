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

from config.dbconfig import get_db_config_by_name
# 枚举统一定义在 permission.operations，这里再导出以保持历史导入路径兼容
from permission.operations import OperationCategory, SQLOperation  # noqa: F401
from permission.roles import ROLE_CATEGORIES, ROLE_SQL_OPERATIONS, Role


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

    def get_role(self, pool_name: str) -> str:
        """Get the role configured for a specific pool.

        非法角色 fail-closed（抛 ConfigurationError），不再静默降级为 readonly。
        """
        config = get_db_config_by_name(pool_name)
        return Role.parse(config.get("role"), pool_name=pool_name).value

    def get_allowed_operations(self, role: str) -> Set[OperationCategory]:
        """Get allowed operation categories for a role."""
        return ROLE_CATEGORIES[Role.parse(role)]

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


class SqlPermissionPolicy(PermissionPolicy):
    """Permission policy for relational databases.

    Maps the readonly/writer/admin roles to allowed SQL operation types.
    """

    def get_role(self, pool_name: str) -> str:
        """Get the role for a specific pool.

        非法角色 fail-closed（抛 ConfigurationError），不再静默降级。
        """
        config = get_db_config_by_name(pool_name)
        return Role.parse(config.get("role"), pool_name=pool_name).value

    def get_allowed_operations(self, role: str) -> Set[SQLOperation]:
        """Get allowed SQL operations for a role."""
        return ROLE_SQL_OPERATIONS[Role.parse(role)]

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
        allowed = self.get_allowed_operations(role)
        unauthorized = operations - allowed

        if unauthorized:
            raise DataSourcePermissionError(
                f"权限不足: 当前角色无权执行以下操作: {', '.join(op.value for op in unauthorized)}"
            )
        return True
