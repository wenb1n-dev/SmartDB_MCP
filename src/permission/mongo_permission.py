"""MongoDB permission policy.

Maps the readonly/writer/admin roles to MongoDB operation categories.
MongoDB operations are classified as READ, WRITE, ADMIN, or DANGEROUS.

Role mapping:
    - ``readonly``: READ operations only (find, aggregate, count, distinct)
    - ``writer``:   READ + WRITE operations (insert, update, delete, findAndModify)
    - ``admin``:    READ + WRITE + ADMIN + DANGEROUS operations
"""

from permission.base import CategoryBasedPermissionPolicy, OperationCategory


_OPERATION_CATEGORIES = {
    # ---- READ operations ----
    "FIND": OperationCategory.READ,
    "AGGREGATE": OperationCategory.READ,
    "COUNT": OperationCategory.READ,
    "DISTINCT": OperationCategory.READ,
    "FINDONE": OperationCategory.READ,
    "MAPREDUCE": OperationCategory.READ,

    # ---- WRITE operations ----
    "INSERT": OperationCategory.WRITE,
    "INSERTMANY": OperationCategory.WRITE,
    "INSERTONE": OperationCategory.WRITE,
    "UPDATE": OperationCategory.WRITE,
    "UPDATEMANY": OperationCategory.WRITE,
    "UPDATEONE": OperationCategory.WRITE,
    "REPLACEONE": OperationCategory.WRITE,
    "FINDANDMODIFY": OperationCategory.WRITE,
    "FINDONEANDUPDATE": OperationCategory.WRITE,
    "FINDONEANDREPLACE": OperationCategory.WRITE,
    "FINDONEANDDELETE": OperationCategory.WRITE,
    "DELETE": OperationCategory.WRITE,
    "DELETEMANY": OperationCategory.WRITE,
    "DELETEONE": OperationCategory.WRITE,
    "REMOVE": OperationCategory.WRITE,
    "BULKWRITE": OperationCategory.WRITE,

    # ---- ADMIN operations ----
    "CREATEINDEX": OperationCategory.ADMIN,
    "CREATEINDEXES": OperationCategory.ADMIN,
    "DROPINDEX": OperationCategory.ADMIN,
    "DROPINDEXES": OperationCategory.ADMIN,
    "REINDEX": OperationCategory.ADMIN,
    "COLLMOD": OperationCategory.ADMIN,
    "RENAMECOLLECTION": OperationCategory.ADMIN,
    "CREATECOLLECTION": OperationCategory.ADMIN,
    "CONVERTTOCAP": OperationCategory.ADMIN,
    "COMPACT": OperationCategory.ADMIN,
    "DBSTATS": OperationCategory.ADMIN,
    "COLLSTATS": OperationCategory.ADMIN,
    "SERVERSTATUS": OperationCategory.ADMIN,
    "CURRENTOP": OperationCategory.ADMIN,
    "KILLOP": OperationCategory.ADMIN,
    "FTDC": OperationCategory.ADMIN,
    "EVAL": OperationCategory.ADMIN,
    "CONNPOOLSYNC": OperationCategory.ADMIN,
    "VACUUM": OperationCategory.ADMIN,

    # ---- DANGEROUS operations ----
    "DROPCOLLECTION": OperationCategory.DANGEROUS,
    "DROP": OperationCategory.DANGEROUS,
    "DROPDATABASE": OperationCategory.DANGEROUS,
    "SHUTDOWN": OperationCategory.DANGEROUS,
    "REPAIRDATABASE": OperationCategory.DANGEROUS,
    "RESYNC": OperationCategory.DANGEROUS,
    "CLEANIANDC": OperationCategory.DANGEROUS,
}

_DANGEROUS_COMMANDS = {
    "DROPCOLLECTION",
    "DROPDATABASE",
    "SHUTDOWN",
    "REPAIRDATABASE",
}


class MongoPermissionPolicy(CategoryBasedPermissionPolicy):
    """Permission policy for MongoDB.

    Maps the readonly/writer/admin roles to allowed MongoDB operation
    categories. Dangerous operations (drop collection, drop database,
    shutdown, etc.) are only allowed for the admin role.
    """

    _OPERATION_CATEGORIES = _OPERATION_CATEGORIES
    _DANGEROUS_COMMANDS = _DANGEROUS_COMMANDS
    _datasource_name = "MongoDB"
