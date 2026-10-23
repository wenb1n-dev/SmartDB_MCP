"""权限决策的结构化审计日志。

所有运行期鉴权决策（允许 / 拒绝）都应通过这里落日志，便于事后审计
「哪个池、以什么角色、被哪个工具、请求了什么操作、为何被拒」。

安全约束：只记录操作分类等元数据，不记录 SQL 正文 / 文档内容 / 命令参数，
避免把敏感数据写入日志。
"""

import json
import logging
import uuid

logger = logging.getLogger("smartdb.authz")


def log_authz_decision(
    *,
    allowed: bool,
    pool_name: str,
    role: str = "",
    tool: str = "",
    paradigm: str = "",
    operations=None,
    reason: str = "",
) -> None:
    """写入一条结构化（JSON 行）鉴权决策日志。

    Args:
        allowed: 是否放行。
        pool_name: 鉴权所针对的连接池（必须等于执行池）。
        role: 解析出的角色。
        tool: 触发鉴权的 MCP 工具名。
        paradigm: 数据源范式。
        operations: 请求的操作标识列表（分类级，不含正文）。
        reason: 拒绝原因（放行时为空）。
    """
    if operations is None:
        operations = []

    requested_ops = [str(op) for op in operations]
    write_operations = {
        "INSERT", "UPDATE", "DELETE", "MERGE", "REPLACE",
        "INSERTONE", "INSERTMANY", "UPDATEONE", "UPDATEMANY",
        "REPLACEONE", "DELETEONE", "DELETEMANY",
        "SET", "LPUSH", "RPUSH", "ZADD", "SADD", "HSET", "DEL",
    }

    payload = {
        "event": "authz",
        "request_id": uuid.uuid4().hex,
        "decision": "allow" if allowed else "deny",
        "pool": pool_name,
        "role": role,
        "tool": tool,
        "paradigm": paradigm,
        "operations": requested_ops,
        "reason": reason,
    }

    # 拒绝一律 WARNING；写操作放行 INFO；只读放行 DEBUG 以控制噪音。
    if not allowed:
        logger.warning(json.dumps(payload, ensure_ascii=False))
    elif any(op in write_operations for op in requested_ops):
        logger.info(json.dumps(payload, ensure_ascii=False))
    else:
        logger.debug(json.dumps(payload, ensure_ascii=False))
