"""Milvus permission policy.

Maps the readonly/writer/admin roles to Milvus operation categories.
Milvus operations are classified as READ, WRITE, ADMIN, or DANGEROUS.

Role mapping:
    - ``readonly``: READ operations only (search, query, get)
    - ``writer``:   READ + WRITE operations (insert, delete, upsert)
    - ``admin``:    READ + WRITE + ADMIN + DANGEROUS operations
"""

from permission.base import CategoryBasedPermissionPolicy, OperationCategory


_OPERATION_CATEGORIES = {
    # ---- READ operations ----
    "SEARCH": OperationCategory.READ,
    "QUERY": OperationCategory.READ,
    "GET": OperationCategory.READ,
    "LIST_COLLECTIONS": OperationCategory.READ,
    "DESCRIBE_COLLECTION": OperationCategory.READ,
    "GET_COLLECTION_STATS": OperationCategory.READ,
    "LIST_INDEXES": OperationCategory.READ,
    "DESCRIBE_INDEX": OperationCategory.READ,
    "GET_INDEX_BUILD_PROGRESS": OperationCategory.READ,
    "GET_QUERY_SEGMENT_INFO": OperationCategory.READ,
    "GET_PERSISTENT_SEGMENT_INFO": OperationCategory.READ,
    "GET_REPLICA": OperationCategory.READ,
    "GET_SERVER_VERSION": OperationCategory.READ,
    "GET_METRICS": OperationCategory.READ,

    # ---- WRITE operations ----
    "INSERT": OperationCategory.WRITE,
    "DELETE": OperationCategory.WRITE,
    "UPSERT": OperationCategory.WRITE,
    "SEARCH_BATCH": OperationCategory.WRITE,
    "HYBRID_SEARCH": OperationCategory.READ,

    # ---- ADMIN operations ----
    "CREATE_COLLECTION": OperationCategory.ADMIN,
    "CREATE_PARTITION": OperationCategory.ADMIN,
    "DROP_PARTITION": OperationCategory.ADMIN,
    "LOAD_COLLECTION": OperationCategory.ADMIN,
    "RELEASE_COLLECTION": OperationCategory.ADMIN,
    "LOAD_PARTITIONS": OperationCategory.ADMIN,
    "RELEASE_PARTITIONS": OperationCategory.ADMIN,
    "CREATE_INDEX": OperationCategory.ADMIN,
    "DROP_INDEX": OperationCategory.ADMIN,
    "FLUSH": OperationCategory.ADMIN,
    "COMPACT": OperationCategory.ADMIN,
    "ALTER_COLLECTION": OperationCategory.ADMIN,
    "RENAME_COLLECTION": OperationCategory.ADMIN,
    "ALTER_INDEX": OperationCategory.ADMIN,
    "ALTER_DATABASE": OperationCategory.ADMIN,

    # ---- DANGEROUS operations ----
    "DROP_COLLECTION": OperationCategory.DANGEROUS,
    "DROP_DATABASE": OperationCategory.DANGEROUS,
    "CREATE_DATABASE": OperationCategory.DANGEROUS,
}

_DANGEROUS_COMMANDS = {
    "DROP_COLLECTION",
    "DROP_DATABASE",
    "CREATE_DATABASE",
}


class MilvusPermissionPolicy(CategoryBasedPermissionPolicy):
    """Permission policy for Milvus.

    Maps the readonly/writer/admin roles to allowed Milvus operation
    categories. Dangerous operations (drop collection, drop database,
    create database) are only allowed for the admin role.
    """

    _OPERATION_CATEGORIES = _OPERATION_CATEGORIES
    _DANGEROUS_COMMANDS = _DANGEROUS_COMMANDS
    _datasource_name = "Milvus"
