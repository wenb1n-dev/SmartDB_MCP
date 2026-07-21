"""Redis permission policy.

Maps the readonly/writer/admin roles to Redis command categories.
Each Redis command is classified as READ, WRITE, ADMIN, or DANGEROUS.

Role mapping:
    - ``readonly``: READ commands only
    - ``writer``    READ + WRITE commands
    - ``admin``     READ + WRITE + ADMIN + DANGEROUS commands
"""

from enum import Enum
from typing import Set

from permission.base import PermissionPolicy


class RedisCommandCategory(str, Enum):
    """Redis command category enumeration."""
    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"
    DANGEROUS = "DANGEROUS"


# Command-to-category mapping
# This is a comprehensive but not exhaustive list of Redis commands.
_COMMAND_CATEGORIES = {
    # ---- READ commands ----
    "GET": RedisCommandCategory.READ,
    "MGET": RedisCommandCategory.READ,
    "HGET": RedisCommandCategory.READ,
    "HGETALL": RedisCommandCategory.READ,
    "HMGET": RedisCommandCategory.READ,
    "HKEYS": RedisCommandCategory.READ,
    "HVALS": RedisCommandCategory.READ,
    "HLEN": RedisCommandCategory.READ,
    "HEXISTS": RedisCommandCategory.READ,
    "HSCAN": RedisCommandCategory.READ,
    "LINDEX": RedisCommandCategory.READ,
    "LRANGE": RedisCommandCategory.READ,
    "LLEN": RedisCommandCategory.READ,
    "LPOS": RedisCommandCategory.READ,
    "SMEMBERS": RedisCommandCategory.READ,
    "SCARD": RedisCommandCategory.READ,
    "SISMEMBER": RedisCommandCategory.READ,
    "SMISMEMBER": RedisCommandCategory.READ,
    "SSCAN": RedisCommandCategory.READ,
    "SRANDMEMBER": RedisCommandCategory.READ,
    "ZRANGE": RedisCommandCategory.READ,
    "ZRANGEBYSCORE": RedisCommandCategory.READ,
    "ZRANGEBYLEX": RedisCommandCategory.READ,
    "ZREVRANGE": RedisCommandCategory.READ,
    "ZREVRANGEBYSCORE": RedisCommandCategory.READ,
    "ZSCORE": RedisCommandCategory.READ,
    "ZMSCORE": RedisCommandCategory.READ,
    "ZRANK": RedisCommandCategory.READ,
    "ZREVRANK": RedisCommandCategory.READ,
    "ZCARD": RedisCommandCategory.READ,
    "ZCOUNT": RedisCommandCategory.READ,
    "ZLEXCOUNT": RedisCommandCategory.READ,
    "ZSCAN": RedisCommandCategory.READ,
    "EXISTS": RedisCommandCategory.READ,
    "TYPE": RedisCommandCategory.READ,
    "TTL": RedisCommandCategory.READ,
    "PTTL": RedisCommandCategory.READ,
    "OBJECT": RedisCommandCategory.READ,
    "STRLEN": RedisCommandCategory.READ,
    "BITCOUNT": RedisCommandCategory.READ,
    "BITPOS": RedisCommandCategory.READ,
    "GETRANGE": RedisCommandCategory.READ,
    "GETBIT": RedisCommandCategory.READ,
    "MEMORY": RedisCommandCategory.READ,
    "DBSIZE": RedisCommandCategory.READ,
    "INFO": RedisCommandCategory.READ,
    "CLIENT": RedisCommandCategory.READ,
    "CLUSTER": RedisCommandCategory.READ,
    "LATENCY": RedisCommandCategory.READ,
    "SLOWLOG": RedisCommandCategory.READ,
    "TIME": RedisCommandCategory.READ,
    "LASTSAVE": RedisCommandCategory.READ,
    "DEBUG": RedisCommandCategory.READ,
    "OBJECT ENCODING": RedisCommandCategory.READ,
    "MEMORY USAGE": RedisCommandCategory.READ,

    # ---- WRITE commands ----
    "SET": RedisCommandCategory.WRITE,
    "SETEX": RedisCommandCategory.WRITE,
    "PSETEX": RedisCommandCategory.WRITE,
    "SETNX": RedisCommandCategory.WRITE,
    "MSET": RedisCommandCategory.WRITE,
    "MSETNX": RedisCommandCategory.WRITE,
    "SETRANGE": RedisCommandCategory.WRITE,
    "APPEND": RedisCommandCategory.WRITE,
    "INCR": RedisCommandCategory.WRITE,
    "DECR": RedisCommandCategory.WRITE,
    "INCRBY": RedisCommandCategory.WRITE,
    "DECRBY": RedisCommandCategory.WRITE,
    "INCRBYFLOAT": RedisCommandCategory.WRITE,
    "HSET": RedisCommandCategory.WRITE,
    "HMSET": RedisCommandCategory.WRITE,
    "HSETNX": RedisCommandCategory.WRITE,
    "HDEL": RedisCommandCategory.WRITE,
    "HINCRBY": RedisCommandCategory.WRITE,
    "HINCRBYFLOAT": RedisCommandCategory.WRITE,
    "LPUSH": RedisCommandCategory.WRITE,
    "RPUSH": RedisCommandCategory.WRITE,
    "LPUSHX": RedisCommandCategory.WRITE,
    "RPUSHX": RedisCommandCategory.WRITE,
    "LPOP": RedisCommandCategory.WRITE,
    "RPOP": RedisCommandCategory.WRITE,
    "LREM": RedisCommandCategory.WRITE,
    "LSET": RedisCommandCategory.WRITE,
    "LTRIM": RedisCommandCategory.WRITE,
    "LINSERT": RedisCommandCategory.WRITE,
    "LMOVE": RedisCommandCategory.WRITE,
    "SADD": RedisCommandCategory.WRITE,
    "SREM": RedisCommandCategory.WRITE,
    "SMOVE": RedisCommandCategory.WRITE,
    "SPOP": RedisCommandCategory.WRITE,
    "SDIFFSTORE": RedisCommandCategory.WRITE,
    "SINTERSTORE": RedisCommandCategory.WRITE,
    "SUNIONSTORE": RedisCommandCategory.WRITE,
    "ZADD": RedisCommandCategory.WRITE,
    "ZREM": RedisCommandCategory.WRITE,
    "ZREMRANGEBYRANK": RedisCommandCategory.WRITE,
    "ZREMRANGEBYSCORE": RedisCommandCategory.WRITE,
    "ZREMRANGEBYLEX": RedisCommandCategory.WRITE,
    "ZINCRBY": RedisCommandCategory.WRITE,
    "ZPOPMAX": RedisCommandCategory.WRITE,
    "ZPOPMIN": RedisCommandCategory.WRITE,
    "DEL": RedisCommandCategory.WRITE,
    "UNLINK": RedisCommandCategory.WRITE,
    "RENAME": RedisCommandCategory.WRITE,
    "RENAMENX": RedisCommandCategory.WRITE,
    "COPY": RedisCommandCategory.WRITE,
    "EXPIRE": RedisCommandCategory.WRITE,
    "PEXPIRE": RedisCommandCategory.WRITE,
    "EXPIREAT": RedisCommandCategory.WRITE,
    "PEXPIREAT": RedisCommandCategory.WRITE,
    "PERSIST": RedisCommandCategory.WRITE,
    "TTL": RedisCommandCategory.READ,
    "SETBIT": RedisCommandCategory.WRITE,
    "GETSET": RedisCommandCategory.WRITE,
    "GETDEL": RedisCommandCategory.WRITE,
    "XADD": RedisCommandCategory.WRITE,
    "XDEL": RedisCommandCategory.WRITE,
    "XTRIM": RedisCommandCategory.WRITE,
    "XACK": RedisCommandCategory.WRITE,
    "GEOADD": RedisCommandCategory.WRITE,
    "GEORADIUSBYMEMBER": RedisCommandCategory.WRITE,
    "BITFIELD": RedisCommandCategory.WRITE,
    "BITOP": RedisCommandCategory.WRITE,

    # ---- ADMIN commands ----
    "CONFIG": RedisCommandCategory.ADMIN,
    "BGSAVE": RedisCommandCategory.ADMIN,
    "BGREWRITEAOF": RedisCommandCategory.ADMIN,
    "SAVE": RedisCommandCategory.ADMIN,
    "REPLICAOF": RedisCommandCategory.ADMIN,
    "SLAVEOF": RedisCommandCategory.ADMIN,
    "MONITOR": RedisCommandCategory.ADMIN,
    "SHUTDOWN": RedisCommandCategory.ADMIN,
    "FLUSHDB": RedisCommandCategory.ADMIN,
    "FLUSHALL": RedisCommandCategory.ADMIN,
    "DBSIZE": RedisCommandCategory.READ,
    "RESET": RedisCommandCategory.ADMIN,
    "SWAPDB": RedisCommandCategory.ADMIN,
    "MEMORY PURGE": RedisCommandCategory.ADMIN,
    "MEMORY MALLOC-STATS": RedisCommandCategory.ADMIN,
    "CLIENT KILL": RedisCommandCategory.ADMIN,
    "CLIENT SETNAME": RedisCommandCategory.ADMIN,
    "CLIENT PAUSE": RedisCommandCategory.ADMIN,
    "ACL": RedisCommandCategory.ADMIN,
    "AUTH": RedisCommandCategory.ADMIN,
    "HELLO": RedisCommandCategory.ADMIN,
    "WAIT": RedisCommandCategory.ADMIN,
    "COMMAND": RedisCommandCategory.ADMIN,
    "FAILOVER": RedisCommandCategory.ADMIN,
}

# Commands that are considered dangerous (destructive or irreversible)
_DANGEROUS_COMMANDS = {
    "FLUSHALL",
    "SHUTDOWN",
    "FLUSHDB",
    "CONFIG",
    "DEBUG",
    "ACL",
}

# Role to allowed categories mapping
_ROLE_CATEGORIES = {
    "readonly": {RedisCommandCategory.READ},
    "writer": {RedisCommandCategory.READ, RedisCommandCategory.WRITE},
    "admin": {
        RedisCommandCategory.READ,
        RedisCommandCategory.WRITE,
        RedisCommandCategory.ADMIN,
        RedisCommandCategory.DANGEROUS,
    },
}


class RedisPermissionPolicy(PermissionPolicy):
    """Permission policy for Redis.

    Maps the readonly/writer/admin roles to allowed Redis command
    categories. Dangerous commands (FLUSHALL, SHUTDOWN, etc.) are only
    allowed for the admin role.
    """

    def get_role(self, pool_name: str) -> str:
        """Get the role configured for a specific Redis pool."""
        from config.dbconfig import get_db_config_by_name
        config = get_db_config_by_name(pool_name)
        return config.get("role", "readonly")

    def get_allowed_operations(self, role: str):
        """Get allowed command categories for a role.

        Returns a set of :class:`RedisCommandCategory` values.
        """
        return _ROLE_CATEGORIES.get(role, _ROLE_CATEGORIES["readonly"])

    def check_permissions(self, pool_name: str, operation) -> bool:
        """Check if the pool's role allows the given Redis command.

        Args:
            pool_name: The connection pool name.
            operation: The Redis command string (e.g., ``"GET"``, ``"FLUSHALL"``).

        Returns:
            True if the command is allowed.

        Raises:
            Exception: When permissions are insufficient.
        """
        from core.exceptions import SQLPermissionError

        command = operation.upper().strip()
        role = self.get_role(pool_name)
        allowed_categories = self.get_allowed_operations(role)

        # Get the category for this command
        category = self._get_command_category(command)

        # Check if the category is allowed
        if category not in allowed_categories:
            raise SQLPermissionError(
                f"权限不足: 当前角色 '{role}' 无权执行 Redis 命令 '{command}' "
                f"(分类: {category.value})"
            )

        return True

    def _get_command_category(self, command: str) -> RedisCommandCategory:
        """Get the category for a Redis command.

        Handles compound commands like ``MEMORY USAGE`` and falls back
        to ADMIN for unknown commands (conservative approach).
        """
        # Check exact match first
        if command in _COMMAND_CATEGORIES:
            return _COMMAND_CATEGORIES[command]

        # Check if it's a dangerous command
        if command in _DANGEROUS_COMMANDS:
            return RedisCommandCategory.DANGEROUS

        # Check compound commands (e.g., "MEMORY USAGE", "CLIENT KILL")
        parts = command.split(None, 1)
        if len(parts) >= 2:
            compound_key = f"{parts[0]} {parts[1]}"
            if compound_key in _COMMAND_CATEGORIES:
                return _COMMAND_CATEGORIES[compound_key]

        # Unknown commands default to ADMIN (conservative: require admin)
        return RedisCommandCategory.ADMIN
