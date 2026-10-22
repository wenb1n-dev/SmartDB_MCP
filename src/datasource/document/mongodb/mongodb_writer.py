"""MongoDB write execution handler.

Executes MongoDB write operations (insert/update/replace/delete) with
permission checking. Supports MongoDB Extended JSON (e.g. ``$oid``,
``$date``) inside documents/filters via ``bson.json_util``.
"""

import json
from typing import Any, Dict, List, Optional

from bson import json_util

from connection.pool_manager import MultiDBPoolManager
from config.dbconfig import get_db_config_by_name


class MongoDBWriteExecutor:
    """Execute MongoDB write operations with permission enforcement."""

    # 支持的写操作及其在权限表中的分类键
    _SUPPORTED_OPERATIONS = {
        "insert_one": "INSERTONE",
        "insert_many": "INSERTMANY",
        "update_one": "UPDATEONE",
        "update_many": "UPDATEMANY",
        "replace_one": "REPLACEONE",
        "delete_one": "DELETEONE",
        "delete_many": "DELETEMANY",
    }

    def __init__(self):
        from permission.mongo_permission import MongoPermissionPolicy
        self._policy = MongoPermissionPolicy()

    @staticmethod
    def _normalize(doc: Any) -> Any:
        """将入参规范化为 BSON 可识别的 Python 对象。

        工具层传入的是普通 JSON（dict/list/标量）。为支持模型用
        MongoDB 扩展 JSON 表达 ObjectId / 日期等类型（如
        ``{"_id": {"$oid": "..."}}``、``{"created_at": {"$date": "..."}}``），
        这里统一 ``json.dumps`` 后再用 ``json_util.loads`` 解析；
        普通 JSON 文档解析结果与原结构一致，不受影响。
        """
        if doc is None:
            return None
        return json_util.loads(json.dumps(doc, ensure_ascii=False))

    def execute_write(
        self,
        pool_name: str,
        collection: str,
        operation: str,
        document: Optional[Dict[str, Any]] = None,
        documents: Optional[List[Dict[str, Any]]] = None,
        filter_doc: Optional[Dict[str, Any]] = None,
        update: Optional[Dict[str, Any]] = None,
        replacement: Optional[Dict[str, Any]] = None,
        upsert: bool = False,
    ) -> str:
        """执行 MongoDB 写操作。

        Args:
            pool_name: 连接池名称。
            collection: 集合名称。
            operation: insert_one/insert_many/update_one/update_many/
                replace_one/delete_one/delete_many 之一。
            document: 单文档（insert_one/replace_one）。
            documents: 文档数组（insert_many）。
            filter_doc: 过滤条件（update/delete/replace）。
            update: 更新表达式，须含 $set/$inc 等更新操作符（update_*）。
            replacement: 替换文档（replace_one，不含操作符）。
            upsert: update/replace 未命中时是否插入，默认 False。

        Returns:
            JSON 格式的执行结果字符串。
        """
        op = operation.lower()
        if op not in self._SUPPORTED_OPERATIONS:
            return (
                f"错误: 不支持的写操作 '{operation}'，支持的操作: "
                f"{', '.join(self._SUPPORTED_OPERATIONS)}"
            )

        # 权限校验（readonly 角色会在此抛出 DataSourcePermissionError）
        self._policy.check_permissions(pool_name, self._SUPPORTED_OPERATIONS[op])

        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        config = get_db_config_by_name(pool_name)
        db_name = config.get("database", "admin")

        # 危险操作防护：update_many / delete_many 必须【显式】传入 filter_doc，
        # 即便过滤条件是空 {} 也要调用方明确给出，防止模型漏传导致全集合误改/误删。
        if op in ("update_many", "delete_many") and filter_doc is None:
            return (
                f"错误: {op} 操作必须显式提供 filter 参数；"
                "如确实要作用于整个集合，请明确传 filter={{}} 并确认已获得授权。"
            )

        with pool.connection() as client:
            coll = client[db_name][collection]
            try:
                if op == "insert_one":
                    if document is None:
                        return "错误: insert_one 需要提供 document 参数"
                    res = coll.insert_one(self._normalize(document))
                    return self._format_result(
                        collection, op,
                        inserted_id=self._oid(res.inserted_id),
                        acknowledged=res.acknowledged,
                    )

                if op == "insert_many":
                    if not documents:
                        return "错误: insert_many 需要提供非空的 documents 数组"
                    res = coll.insert_many(self._normalize(documents))
                    return self._format_result(
                        collection, op,
                        inserted_count=len(res.inserted_ids),
                        inserted_ids=[self._oid(i) for i in res.inserted_ids],
                        acknowledged=res.acknowledged,
                    )

                if op == "update_one":
                    if filter_doc is None or update is None:
                        return "错误: update_one 需要同时提供 filter 与 update 参数"
                    res = coll.update_one(
                        self._normalize(filter_doc),
                        self._normalize(update),
                        upsert=upsert,
                    )
                    return self._format_result(
                        collection, op,
                        matched_count=res.matched_count,
                        modified_count=res.modified_count,
                        upserted_id=self._oid(res.upserted_id) if res.upserted_id else None,
                        acknowledged=res.acknowledged,
                    )

                if op == "update_many":
                    if update is None:
                        return "错误: update_many 需要提供 update 参数"
                    res = coll.update_many(
                        self._normalize(filter_doc),
                        self._normalize(update),
                        upsert=upsert,
                    )
                    return self._format_result(
                        collection, op,
                        matched_count=res.matched_count,
                        modified_count=res.modified_count,
                        upserted_id=self._oid(res.upserted_id) if res.upserted_id else None,
                        acknowledged=res.acknowledged,
                    )

                if op == "replace_one":
                    if filter_doc is None or replacement is None:
                        return "错误: replace_one 需要同时提供 filter 与 replacement 参数"
                    res = coll.replace_one(
                        self._normalize(filter_doc),
                        self._normalize(replacement),
                        upsert=upsert,
                    )
                    return self._format_result(
                        collection, op,
                        matched_count=res.matched_count,
                        modified_count=res.modified_count,
                        upserted_id=self._oid(res.upserted_id) if res.upserted_id else None,
                        acknowledged=res.acknowledged,
                    )

                if op == "delete_one":
                    if filter_doc is None:
                        return "错误: delete_one 需要提供 filter 参数"
                    res = coll.delete_one(self._normalize(filter_doc))
                    return self._format_result(
                        collection, op,
                        deleted_count=res.deleted_count,
                        acknowledged=res.acknowledged,
                    )

                # delete_many（filter 显式性已在前面校验）
                res = coll.delete_many(self._normalize(filter_doc))
                return self._format_result(
                    collection, op,
                    deleted_count=res.deleted_count,
                    acknowledged=res.acknowledged,
                )

            except Exception as e:
                return f"写入执行失败: {str(e)}"

    @staticmethod
    def _oid(value: Any) -> Optional[str]:
        """将 ObjectId 安全转为字符串，非 ObjectId 原样返回。"""
        if value is None:
            return None
        return str(value)

    def _format_result(self, collection: str, operation: str, **fields: Any) -> str:
        """统一格式化写操作返回结果（JSON）。"""
        result = {"collection": collection, "operation": operation}
        result.update({k: v for k, v in fields.items() if v is not None})
        return json.dumps(result, ensure_ascii=False, indent=2, default=json_util.default)
