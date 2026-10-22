"""Kafka permission policy.

Maps the readonly/writer/admin roles to Kafka operation categories.
Kafka operations are classified as READ, WRITE, ADMIN, or DANGEROUS.

Role mapping:
    - ``readonly``: READ operations only (list topics, describe, consumer lag)
    - ``writer``:   READ + WRITE operations (produce, create topics)
    - ``admin``:    READ + WRITE + ADMIN + DANGEROUS operations
"""

from permission.base import CategoryBasedPermissionPolicy, OperationCategory


_OPERATION_CATEGORIES = {
    # ---- READ operations ----
    "LIST_TOPICS": OperationCategory.READ,
    "DESCRIBE_TOPIC": OperationCategory.READ,
    "DESCRIBE_GROUP": OperationCategory.READ,
    "LIST_GROUPS": OperationCategory.READ,
    "CONSUME": OperationCategory.READ,
    "GET_OFFSETS": OperationCategory.READ,
    "GET_CONSUMER_LAG": OperationCategory.READ,
    "DESCRIBE_CLUSTER": OperationCategory.READ,
    "DESCRIBE_BROKERS": OperationCategory.READ,
    "DESCRIBE_LOG_DIRS": OperationCategory.READ,
    "DESCRIBE_CONFIGS": OperationCategory.READ,

    # ---- WRITE operations ----
    "PRODUCE": OperationCategory.WRITE,
    "COMMIT_OFFSET": OperationCategory.WRITE,
    "ALTER_CONSUMER_OFFSET": OperationCategory.WRITE,

    # ---- ADMIN operations ----
    "CREATE_TOPIC": OperationCategory.ADMIN,
    "ALTER_TOPIC": OperationCategory.ADMIN,
    "CREATE_PARTITION": OperationCategory.ADMIN,
    "ALTER_CONFIGS": OperationCategory.ADMIN,
    "CREATE_ACL": OperationCategory.ADMIN,
    "DELETE_ACL": OperationCategory.ADMIN,
    "ALTER_CLIENT_QUOTAS": OperationCategory.ADMIN,

    # ---- DANGEROUS operations ----
    "DELETE_TOPIC": OperationCategory.DANGEROUS,
    "DELETE_GROUP": OperationCategory.DANGEROUS,
    "DELETE_RECORDS": OperationCategory.DANGEROUS,
}

_DANGEROUS_COMMANDS = {
    "DELETE_TOPIC",
    "DELETE_GROUP",
    "DELETE_RECORDS",
}


class KafkaPermissionPolicy(CategoryBasedPermissionPolicy):
    """Permission policy for Kafka.

    Maps the readonly/writer/admin roles to allowed Kafka operation
    categories. Dangerous operations (delete topic, delete group,
    delete records) are only allowed for the admin role.
    """

    _OPERATION_CATEGORIES = _OPERATION_CATEGORIES
    _DANGEROUS_COMMANDS = _DANGEROUS_COMMANDS
    _datasource_name = "Kafka"
