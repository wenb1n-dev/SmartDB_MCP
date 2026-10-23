"""MCP 工具到权限声明的集中映射。

所有对外工具必须在此声明权限意图；未声明的新工具会在服务调用入口 fail-closed。
"""

from __future__ import annotations

from datasource.base import Paradigm
from permission.guard import (
    PermissionSpec,
    es_query_operations,
    fixed_category_operation,
    kafka_consumer_lag_operations,
    metadata_sql_operations,
    mongo_query_operations,
    mongo_write_operations,
    redis_command_operations,
    sql_query_operations,
)


# 通用工具：根据目标池实际范式动态鉴权
_COMMON_METADATA_SPEC = PermissionSpec(dynamic_paradigm=True)

# 关系型元数据/诊断工具：统一按 SELECT 只读权限处理
_RELATIONAL_METADATA_SPEC = PermissionSpec(
    paradigm=Paradigm.RELATIONAL,
    sql_resolver=metadata_sql_operations,
)

TOOL_PERMISSION_SPECS = {
    # 通用工具
    "get_db_health": _COMMON_METADATA_SPEC,
    "get_db_version": _COMMON_METADATA_SPEC,

    # 关系型工具
    "execute_sql": PermissionSpec(
        paradigm=Paradigm.RELATIONAL,
        sql_resolver=sql_query_operations,
    ),
    "sql_creator": _RELATIONAL_METADATA_SPEC,
    "sql_optimize": PermissionSpec(
        paradigm=Paradigm.RELATIONAL,
        sql_resolver=sql_query_operations,
    ),
    "get_table_name": _RELATIONAL_METADATA_SPEC,
    "get_table_desc": _RELATIONAL_METADATA_SPEC,
    "get_table_index": _RELATIONAL_METADATA_SPEC,

    # Redis KV 工具
    "execute_command": PermissionSpec(
        paradigm=Paradigm.KV_STORE,
        category_resolver=redis_command_operations,
    ),
    "get_key_info": PermissionSpec(
        paradigm=Paradigm.KV_STORE,
        category_resolver=fixed_category_operation("GET"),
    ),
    "scan_keys": PermissionSpec(
        paradigm=Paradigm.KV_STORE,
        category_resolver=fixed_category_operation("SSCAN"),
    ),

    # MongoDB 文档工具
    "execute_mongo_query": PermissionSpec(
        paradigm=Paradigm.DOCUMENT,
        category_resolver=mongo_query_operations,
    ),
    "execute_mongo_write": PermissionSpec(
        paradigm=Paradigm.DOCUMENT,
        category_resolver=mongo_write_operations,
    ),
    "mongo_explain": PermissionSpec(
        paradigm=Paradigm.DOCUMENT,
        category_resolver=mongo_query_operations,
    ),
    "get_collection_names": PermissionSpec(
        paradigm=Paradigm.DOCUMENT,
        category_resolver=fixed_category_operation("COUNT"),
    ),
    "get_collection_schema": PermissionSpec(
        paradigm=Paradigm.DOCUMENT,
        category_resolver=fixed_category_operation("FIND"),
    ),
    "get_collection_indexes": PermissionSpec(
        paradigm=Paradigm.DOCUMENT,
        category_resolver=fixed_category_operation("COUNT"),
    ),

    # Milvus 向量工具
    "execute_vector_search": PermissionSpec(
        paradigm=Paradigm.VECTOR,
        category_resolver=fixed_category_operation("SEARCH"),
    ),
    "get_collection_info": PermissionSpec(
        paradigm=Paradigm.VECTOR,
        category_resolver=fixed_category_operation("DESCRIBE_COLLECTION"),
    ),
    "get_vector_index_info": PermissionSpec(
        paradigm=Paradigm.VECTOR,
        category_resolver=fixed_category_operation("DESCRIBE_INDEX"),
    ),

    # Elasticsearch 搜索工具
    "execute_es_query": PermissionSpec(
        paradigm=Paradigm.SEARCH_ENGINE,
        category_resolver=es_query_operations,
    ),
    "get_index_names": PermissionSpec(
        paradigm=Paradigm.SEARCH_ENGINE,
        category_resolver=fixed_category_operation("INDICES"),
    ),
    "get_index_mapping": PermissionSpec(
        paradigm=Paradigm.SEARCH_ENGINE,
        category_resolver=fixed_category_operation("GET_MAPPING"),
    ),

    # Kafka 消息队列工具
    "list_topics": PermissionSpec(
        paradigm=Paradigm.MESSAGE_QUEUE,
        category_resolver=fixed_category_operation("LIST_TOPICS"),
    ),
    "get_topic_info": PermissionSpec(
        paradigm=Paradigm.MESSAGE_QUEUE,
        category_resolver=fixed_category_operation("DESCRIBE_TOPIC"),
    ),
    "get_consumer_lag": PermissionSpec(
        paradigm=Paradigm.MESSAGE_QUEUE,
        category_resolver=kafka_consumer_lag_operations,
    ),
}
