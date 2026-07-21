"""MongoDB permission policy.

Maps the readonly/writer/admin roles to MongoDB operation categories.
MongoDB operations are classified as READ, WRITE, ADMIN, or DANGEROUS.

Role mapping:
    - ``readonly``: READ operations only (find, aggregate, count, distinct)
    - ``writer``:   READ + WRITE operations (insert, update, delete, findAndModify)
    - ``admin``:    READ + WRITE + ADMIN + DANGEROUS operations
"""

from enum import Enum
from typing import Set

from permission.base import PermissionPolicy


class MongoOperationCategory(str, Enum):
    """MongoDB operation category enumeration."""
    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"
    DANGEROUS = "DANGEROUS"


# Operation-to-category mapping
# Maps MongoDB operation names to their categories.
_OPERATION_CATEGORIES = {
    # ---- READ operations ----
    "FIND": MongoOperationCategory.READ,
    "AGGREGATE": MongoOperationCategory.READ,
    "COUNT": MongoOperationCategory.READ,
    "DISTINCT": MongoOperationCategory.READ,
    "FINDONE": MongoOperationCategory.READ,
    "MAPREDUCE": MongoOperationCategory.READ,

    # ---- WRITE operations ----
    "INSERT": MongoOperationCategory.WRITE,
    "INSERTMANY": MongoOperationCategory.WRITE,
    "INSERTONE": MongoOperationCategory.WRITE,
    "UPDATE": MongoOperationCategory.WRITE,
    "UPDATEMANY": MongoOperationCategory.WRITE,
    "UPDATEONE": MongoOperationCategory.WRITE,
    "REPLACEONE": MongoOperationCategory.WRITE,
    "FINDANDMODIFY": MongoOperationCategory.WRITE,
    "FINDONEANDUPDATE": MongoOperationCategory.WRITE,
    "FINDONEANDREPLACE": MongoOperationCategory.WRITE,
    "FINDONEANDDELETE": MongoOperationCategory.WRITE,
    "DELETE": MongoOperationCategory.WRITE,
    "DELETEMANY": MongoOperationCategory.WRITE,
    "DELETEONE": MongoOperationCategory.WRITE,
    "REMOVE": MongoOperationCategory.WRITE,
    "BULKWRITE": MongoOperationCategory.WRITE,

    # ---- ADMIN operations ----
    "CREATEINDEX": MongoOperationCategory.ADMIN,
    "CREATEINDEXES": MongoOperationCategory.ADMIN,
    "DROPINDEX": MongoOperationCategory.ADMIN,
    "DROPINDEXES": MongoOperationCategory.ADMIN,
    "REINDEX": MongoOperationCategory.ADMIN,
    "COLLMOD": MongoOperationCategory.ADMIN,
    "RENAMECOLLECTION": MongoOperationCategory.ADMIN,
    "CREATECOLLECTION": MongoOperationCategory.ADMIN,
    "CONVERTTOCAP": MongoOperationCategory.ADMIN,
    "COMPACT": MongoOperationCategory.ADMIN,
    "DBSTATS": MongoOperationCategory.ADMIN,
    "COLLSTATS": MongoOperationCategory.ADMIN,
    "SERVERSTATUS": MongoOperationCategory.ADMIN,
    "CURRENTOP": MongoOperationCategory.ADMIN,
    "KILLOP": MongoOperationCategory.ADMIN,
    "FTDC": MongoOperationCategory.ADMIN,
    "EVAL": MongoOperationCategory.ADMIN,
    "CONNPOOLSYNC": MongoOperationCategory.ADMIN,
    "VACUUM": MongoOperationCategory.ADMIN,

    # ---- DANGEROUS operations ----
    "DROPCOLLECTION": MongoOperationCategory.DANGEROUS,
    "DROP": MongoOperationCategory.DANGEROUS,
    "DROPDATABASE": MongoOperationCategory.DANGEROUS,
    "SHUTDOWN": MongoOperationCategory.DANGEROUS,
    "REPAIRDATABASE": MongoOperationCategory.DANGEROUS,
    "RESYNC": MongoOperationCategory.DANGEROUS,
    "CLEANIANDC": MongoOperationCategory.DANGEROUS,
}

# Commands that are considered dangerous (destructive or irreversible)
_DANGEROUS_COMMANDS = {
    "DROPCOLLECTION",
    "DROPDATABASE",
    "SHUTDOWN",
    "REPAIRDATABASE",
}

# Role to allowed categories mapping
_ROLE_CATEGORIES = {
    "readonly": {MongoOperationCategory.READ},
    "writer": {MongoOperationCategory.READ, MongoOperationCategory.WRITE},
    "admin": {
        MongoOperationCategory.READ,
        MongoOperationCategory.WRITE,
        MongoOperationCategory.ADMIN,
        MongoOperationCategory.DANGEROUS,
    },
}


class MongoPermissionPolicy(PermissionPolicy):
    """Permission policy for MongoDB.

    Maps the readonly/writer/admin roles to allowed MongoDB operation
    categories. Dangerous operations (drop collection, drop database,
    shutdown, etc.) are only allowed for the admin role.
    """

    def get_role(self, pool_name: str) -> str:
        """Get the role configured for a specific MongoDB pool."""
        from config.dbconfig import get_db_config_by_name
        config = get_db_config_by_name(pool_name)
        return config.get("role", "readonly")

    def get_allowed_operations(self, role: str) -> Set[MongoOperationCategory]:
        """Get allowed operation categories for a role.

        Returns a set of :class:`MongoOperationCategory` values.
        """
        return _ROLE_CATEGORIES.get(role, _ROLE_CATEGORIES["readonly"])

    def check_permissions(self, pool_name: str, operation) -> bool:
        """Check if the pool's role allows the given MongoDB operation.

        Args:
            pool_name: The connection pool name.
            operation: The MongoDB operation string (e.g., ``"FIND"``, ``"INSERT"``).

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
                f"权限不足: 当前角色 '{role}' 无权执行 MongoDB 操作 '{operation_upper}' "
                f"(分类: {category.value})"
            )

        return True

    def _get_operation_category(self, operation: str) -> MongoOperationCategory:
        """Get the category for a MongoDB operation.

        Falls back to ADMIN for unknown operations (conservative approach).
        """
        # Check exact match
        if operation in _OPERATION_CATEGORIES:
            return _OPERATION_CATEGORIES[operation]

        # Check if it's a dangerous command
        if operation in _DANGEROUS_COMMANDS:
            return MongoOperationCategory.DANGEROUS

        # Unknown commands default to ADMIN (conservative: require admin)
        return MongoOperationCategory.ADMIN
