"""Elasticsearch permission policy.

Maps the readonly/writer/admin roles to Elasticsearch operation categories.
ES operations are classified as READ, WRITE, ADMIN, or DANGEROUS.

Role mapping:
    - ``readonly``: READ operations only (search, count, aggregate, get mapping)
    - ``writer``:   READ + WRITE operations (index, update, delete, bulk)
    - ``admin``:    READ + WRITE + ADMIN + DANGEROUS operations
"""

from permission.base import CategoryBasedPermissionPolicy, OperationCategory


_OPERATION_CATEGORIES = {
    # ---- READ operations ----
    "SEARCH": OperationCategory.READ,
    "COUNT": OperationCategory.READ,
    "AGGREGATE": OperationCategory.READ,
    "GET": OperationCategory.READ,
    "MGET": OperationCategory.READ,
    "GET_MAPPING": OperationCategory.READ,
    "GET_SETTINGS": OperationCategory.READ,
    "GET_INDEX": OperationCategory.READ,
    "EXISTS": OperationCategory.READ,
    "COUNT_PERC": OperationCategory.READ,
    "TERMVECTORS": OperationCategory.READ,
    "MTERMVECTORS": OperationCategory.READ,
    "EXPLAIN": OperationCategory.READ,
    "FIELD_CAPS": OperationCategory.READ,
    "MAPPINGS": OperationCategory.READ,
    "INDICES": OperationCategory.READ,

    # ---- WRITE operations ----
    "INDEX": OperationCategory.WRITE,
    "UPDATE": OperationCategory.WRITE,
    "DELETE": OperationCategory.WRITE,
    "BULK": OperationCategory.WRITE,
    "UPDATE_BY_QUERY": OperationCategory.WRITE,
    "DELETE_BY_QUERY": OperationCategory.WRITE,
    "REINDEX": OperationCategory.WRITE,

    # ---- ADMIN operations ----
    "CREATE_INDEX": OperationCategory.ADMIN,
    "PUT_MAPPING": OperationCategory.ADMIN,
    "PUT_SETTINGS": OperationCategory.ADMIN,
    "OPEN": OperationCategory.ADMIN,
    "CLOSE": OperationCategory.ADMIN,
    "REFRESH": OperationCategory.ADMIN,
    "FLUSH": OperationCategory.ADMIN,
    "FORCED_MERGE": OperationCategory.ADMIN,
    "CLEAR_CACHE": OperationCategory.ADMIN,
    "CLONE": OperationCategory.ADMIN,
    "SPLIT": OperationCategory.ADMIN,
    "SHRINK": OperationCategory.ADMIN,
    "RELOCATE": OperationCategory.ADMIN,
    "REROUTE": OperationCategory.ADMIN,
    "PUT_TEMPLATE": OperationCategory.ADMIN,
    "PUT_ALIAS": OperationCategory.ADMIN,

    # ---- DANGEROUS operations ----
    "DELETE_INDEX": OperationCategory.DANGEROUS,
    "DELETE_INDEX_TEMPLATE": OperationCategory.DANGEROUS,
    "DELETE_ALIAS": OperationCategory.DANGEROUS,
}

_DANGEROUS_COMMANDS = {
    "DELETE_INDEX",
    "DELETE_INDEX_TEMPLATE",
    "DELETE_ALIAS",
}


class ESPermissionPolicy(CategoryBasedPermissionPolicy):
    """Permission policy for Elasticsearch.

    Maps the readonly/writer/admin roles to allowed ES operation
    categories. Dangerous operations (delete index, delete template,
    delete alias) are only allowed for the admin role.
    """

    _OPERATION_CATEGORIES = _OPERATION_CATEGORIES
    _DANGEROUS_COMMANDS = _DANGEROUS_COMMANDS
    _datasource_name = "Elasticsearch"
