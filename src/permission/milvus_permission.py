"""Milvus permission policy.

Maps the readonly/writer/admin roles to Milvus operation categories.
Milvus operations are classified as READ, WRITE, ADMIN, or DANGEROUS.

Role mapping:
    - ``readonly``: READ operations only (search, query, get)
    - ``writer``:   READ + WRITE operations (insert, delete, upsert)
    - ``admin``:    READ + WRITE + ADMIN + DANGEROUS operations
"""

from enum import Enum
from typing import Set

from permission.base import PermissionPolicy


class MilvusOperationCategory(str, Enum):
    """Milvus operation category enumeration."""
    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"
    DANGEROUS = "DANGEROUS"


# Operation-to-category mapping
_OPERATION_CATEGORIES = {
    # ---- READ operations ----
    "SEARCH": MilvusOperationCategory.READ,
    "QUERY": MilvusOperationCategory.READ,
    "GET": MilvusOperationCategory.READ,
    "LIST_COLLECTIONS": MilvusOperationCategory.READ,
    "DESCRIBE_COLLECTION": MilvusOperationCategory.READ,
    "GET_COLLECTION_STATS": MilvusOperationCategory.READ,
    "LIST_INDEXES": MilvusOperationCategory.READ,
    "DESCRIBE_INDEX": MilvusOperationCategory.READ,
    "GET_INDEX_BUILD_PROGRESS": MilvusOperationCategory.READ,
    "GET_QUERY_SEGMENT_INFO": MilvusOperationCategory.READ,
    "GET_PERSISTENT_SEGMENT_INFO": MilvusOperationCategory.READ,
    "GET_REPLICA": MilvusOperationCategory.READ,
    "GET_SERVER_VERSION": MilvusOperationCategory.READ,
    "GET_METRICS": MilvusOperationCategory.READ,

    # ---- WRITE operations ----
    "INSERT": MilvusOperationCategory.WRITE,
    "DELETE": MilvusOperationCategory.WRITE,
    "UPSERT": MilvusOperationCategory.WRITE,
    "SEARCH_BATCH": MilvusOperationCategory.WRITE,
    "HYBRID_SEARCH": MilvusOperationCategory.READ,

    # ---- ADMIN operations ----
    "CREATE_COLLECTION": MilvusOperationCategory.ADMIN,
    "CREATE_PARTITION": MilvusOperationCategory.ADMIN,
    "DROP_PARTITION": MilvusOperationCategory.ADMIN,
    "LOAD_COLLECTION": MilvusOperationCategory.ADMIN,
    "RELEASE_COLLECTION": MilvusOperationCategory.ADMIN,
    "LOAD_PARTITIONS": MilvusOperationCategory.ADMIN,
    "RELEASE_PARTITIONS": MilvusOperationCategory.ADMIN,
    "CREATE_INDEX": MilvusOperationCategory.ADMIN,
    "DROP_INDEX": MilvusOperationCategory.ADMIN,
    "FLUSH": MilvusOperationCategory.ADMIN,
    "COMPACT": MilvusOperationCategory.ADMIN,
    "ALTER_COLLECTION": MilvusOperationCategory.ADMIN,
    "RENAME_COLLECTION": MilvusOperationCategory.ADMIN,
    "ALTER_INDEX": MilvusOperationCategory.ADMIN,
    "ALTER_DATABASE": MilvusOperationCategory.ADMIN,

    # ---- DANGEROUS operations ----
    "DROP_COLLECTION": MilvusOperationCategory.DANGEROUS,
    "DROP_DATABASE": MilvusOperationCategory.DANGEROUS,
    "CREATE_DATABASE": MilvusOperationCategory.DANGEROUS,
}

# Commands that are considered dangerous (destructive or irreversible)
_DANGEROUS_COMMANDS = {
    "DROP_COLLECTION",
    "DROP_DATABASE",
    "CREATE_DATABASE",
}

# Role to allowed categories mapping
_ROLE_CATEGORIES = {
    "readonly": {MilvusOperationCategory.READ},
    "writer": {MilvusOperationCategory.READ, MilvusOperationCategory.WRITE},
    "admin": {
        MilvusOperationCategory.READ,
        MilvusOperationCategory.WRITE,
        MilvusOperationCategory.ADMIN,
        MilvusOperationCategory.DANGEROUS,
    },
}


class MilvusPermissionPolicy(PermissionPolicy):
    """Permission policy for Milvus.

    Maps the readonly/writer/admin roles to allowed Milvus operation
    categories. Dangerous operations (drop collection, drop database,
    create database) are only allowed for the admin role.
    """

    def get_role(self, pool_name: str) -> str:
        """Get the role configured for a specific Milvus pool."""
        from config.dbconfig import get_db_config_by_name
        config = get_db_config_by_name(pool_name)
        return config.get("role", "readonly")

    def get_allowed_operations(self, role: str) -> Set[MilvusOperationCategory]:
        """Get allowed operation categories for a role.

        Returns a set of :class:`MilvusOperationCategory` values.
        """
        return _ROLE_CATEGORIES.get(role, _ROLE_CATEGORIES["readonly"])

    def check_permissions(self, pool_name: str, operation) -> bool:
        """Check if the pool's role allows the given Milvus operation.

        Args:
            pool_name: The connection pool name.
            operation: The Milvus operation string (e.g., ``"SEARCH"``, ``"INSERT"``).

        Returns:
            True if the operation is allowed.

        Raises:
            Exception: When permissions are insufficient.
        """
        from core.exceptions import SQLPermissionError

        operation_upper = operation.upper().strip()
        role = self.get_role(pool_name)
        allowed_categories = self.get_allowed_operations(role)

        # Get the category for this operation
        category = self._get_operation_category(operation_upper)

        # Check if the category is allowed
        if category not in allowed_categories:
            raise SQLPermissionError(
                f"权限不足: 当前角色 '{role}' 无权执行 Milvus 操作 '{operation_upper}' "
                f"(分类: {category.value})"
            )

        return True

    def _get_operation_category(self, operation: str) -> MilvusOperationCategory:
        """Get the category for a Milvus operation.

        Falls back to ADMIN for unknown operations (conservative approach).
        """
        # Check exact match
        if operation in _OPERATION_CATEGORIES:
            return _OPERATION_CATEGORIES[operation]

        # Check if it's a dangerous command
        if operation in _DANGEROUS_COMMANDS:
            return MilvusOperationCategory.DANGEROUS

        # Unknown commands default to ADMIN (conservative: require admin)
        return MilvusOperationCategory.ADMIN
