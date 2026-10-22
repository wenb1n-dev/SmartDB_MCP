"""Redis permission policy.

Maps the readonly/writer/admin roles to Redis command categories.
Each Redis command is classified as READ, WRITE, ADMIN, or DANGEROUS.

Role mapping:
    - ``readonly``: READ commands only
    - ``writer``    READ + WRITE commands
    - ``admin``     READ + WRITE + ADMIN + DANGEROUS commands
"""

from permission.base import CategoryBasedPermissionPolicy, OperationCategory


# Command-to-category mapping
_COMMAND_CATEGORIES = {
    # ---- READ commands ----
    "GET": OperationCategory.READ,
    "MGET": OperationCategory.READ,
    "HGET": OperationCategory.READ,
    "HGETALL": OperationCategory.READ,
    "HMGET": OperationCategory.READ,
    "HKEYS": OperationCategory.READ,
    "HVALS": OperationCategory.READ,
    "HLEN": OperationCategory.READ,
    "HEXISTS": OperationCategory.READ,
    "HSCAN": OperationCategory.READ,
    "LINDEX": OperationCategory.READ,
    "LRANGE": OperationCategory.READ,
    "LLEN": OperationCategory.READ,
    "LPOS": OperationCategory.READ,
    "SMEMBERS": OperationCategory.READ,
    "SCARD": OperationCategory.READ,
    "SISMEMBER": OperationCategory.READ,
    "SMISMEMBER": OperationCategory.READ,
    "SSCAN": OperationCategory.READ,
    "SRANDMEMBER": OperationCategory.READ,
    "ZRANGE": OperationCategory.READ,
    "ZRANGEBYSCORE": OperationCategory.READ,
    "ZRANGEBYLEX": OperationCategory.READ,
    "ZREVRANGE": OperationCategory.READ,
    "ZREVRANGEBYSCORE": OperationCategory.READ,
    "ZSCORE": OperationCategory.READ,
    "ZMSCORE": OperationCategory.READ,
    "ZRANK": OperationCategory.READ,
    "ZREVRANK": OperationCategory.READ,
    "ZCARD": OperationCategory.READ,
    "ZCOUNT": OperationCategory.READ,
    "ZLEXCOUNT": OperationCategory.READ,
    "ZSCAN": OperationCategory.READ,
    "EXISTS": OperationCategory.READ,
    "TYPE": OperationCategory.READ,
    "TTL": OperationCategory.READ,
    "PTTL": OperationCategory.READ,
    "OBJECT": OperationCategory.READ,
    "STRLEN": OperationCategory.READ,
    "BITCOUNT": OperationCategory.READ,
    "BITPOS": OperationCategory.READ,
    "GETRANGE": OperationCategory.READ,
    "GETBIT": OperationCategory.READ,
    "MEMORY": OperationCategory.READ,
    "DBSIZE": OperationCategory.READ,
    "INFO": OperationCategory.READ,
    "CLIENT": OperationCategory.READ,
    "CLUSTER": OperationCategory.READ,
    "LATENCY": OperationCategory.READ,
    "SLOWLOG": OperationCategory.READ,
    "TIME": OperationCategory.READ,
    "LASTSAVE": OperationCategory.READ,
    "DEBUG": OperationCategory.READ,
    "OBJECT ENCODING": OperationCategory.READ,
    "MEMORY USAGE": OperationCategory.READ,

    # ---- WRITE commands ----
    "SET": OperationCategory.WRITE,
    "SETEX": OperationCategory.WRITE,
    "PSETEX": OperationCategory.WRITE,
    "SETNX": OperationCategory.WRITE,
    "MSET": OperationCategory.WRITE,
    "MSETNX": OperationCategory.WRITE,
    "SETRANGE": OperationCategory.WRITE,
    "APPEND": OperationCategory.WRITE,
    "INCR": OperationCategory.WRITE,
    "DECR": OperationCategory.WRITE,
    "INCRBY": OperationCategory.WRITE,
    "DECRBY": OperationCategory.WRITE,
    "INCRBYFLOAT": OperationCategory.WRITE,
    "HSET": OperationCategory.WRITE,
    "HMSET": OperationCategory.WRITE,
    "HSETNX": OperationCategory.WRITE,
    "HDEL": OperationCategory.WRITE,
    "HINCRBY": OperationCategory.WRITE,
    "HINCRBYFLOAT": OperationCategory.WRITE,
    "LPUSH": OperationCategory.WRITE,
    "RPUSH": OperationCategory.WRITE,
    "LPUSHX": OperationCategory.WRITE,
    "RPUSHX": OperationCategory.WRITE,
    "LPOP": OperationCategory.WRITE,
    "RPOP": OperationCategory.WRITE,
    "LREM": OperationCategory.WRITE,
    "LSET": OperationCategory.WRITE,
    "LTRIM": OperationCategory.WRITE,
    "LINSERT": OperationCategory.WRITE,
    "LMOVE": OperationCategory.WRITE,
    "SADD": OperationCategory.WRITE,
    "SREM": OperationCategory.WRITE,
    "SMOVE": OperationCategory.WRITE,
    "SPOP": OperationCategory.WRITE,
    "SDIFFSTORE": OperationCategory.WRITE,
    "SINTERSTORE": OperationCategory.WRITE,
    "SUNIONSTORE": OperationCategory.WRITE,
    "ZADD": OperationCategory.WRITE,
    "ZREM": OperationCategory.WRITE,
    "ZREMRANGEBYRANK": OperationCategory.WRITE,
    "ZREMRANGEBYSCORE": OperationCategory.WRITE,
    "ZREMRANGEBYLEX": OperationCategory.WRITE,
    "ZINCRBY": OperationCategory.WRITE,
    "ZPOPMAX": OperationCategory.WRITE,
    "ZPOPMIN": OperationCategory.WRITE,
    "DEL": OperationCategory.WRITE,
    "UNLINK": OperationCategory.WRITE,
    "RENAME": OperationCategory.WRITE,
    "RENAMENX": OperationCategory.WRITE,
    "COPY": OperationCategory.WRITE,
    "EXPIRE": OperationCategory.WRITE,
    "PEXPIRE": OperationCategory.WRITE,
    "EXPIREAT": OperationCategory.WRITE,
    "PEXPIREAT": OperationCategory.WRITE,
    "PERSIST": OperationCategory.WRITE,
    "SETBIT": OperationCategory.WRITE,
    "GETSET": OperationCategory.WRITE,
    "GETDEL": OperationCategory.WRITE,
    "XADD": OperationCategory.WRITE,
    "XDEL": OperationCategory.WRITE,
    "XTRIM": OperationCategory.WRITE,
    "XACK": OperationCategory.WRITE,
    "GEOADD": OperationCategory.WRITE,
    "GEORADIUSBYMEMBER": OperationCategory.WRITE,
    "BITFIELD": OperationCategory.WRITE,
    "BITOP": OperationCategory.WRITE,

    # ---- ADMIN commands ----
    "CONFIG": OperationCategory.ADMIN,
    "BGSAVE": OperationCategory.ADMIN,
    "BGREWRITEAOF": OperationCategory.ADMIN,
    "SAVE": OperationCategory.ADMIN,
    "REPLICAOF": OperationCategory.ADMIN,
    "SLAVEOF": OperationCategory.ADMIN,
    "MONITOR": OperationCategory.ADMIN,
    "SHUTDOWN": OperationCategory.ADMIN,
    "FLUSHDB": OperationCategory.ADMIN,
    "FLUSHALL": OperationCategory.ADMIN,
    "RESET": OperationCategory.ADMIN,
    "SWAPDB": OperationCategory.ADMIN,
    "MEMORY PURGE": OperationCategory.ADMIN,
    "MEMORY MALLOC-STATS": OperationCategory.ADMIN,
    "CLIENT KILL": OperationCategory.ADMIN,
    "CLIENT SETNAME": OperationCategory.ADMIN,
    "CLIENT PAUSE": OperationCategory.ADMIN,
    "ACL": OperationCategory.ADMIN,
    "AUTH": OperationCategory.ADMIN,
    "HELLO": OperationCategory.ADMIN,
    "WAIT": OperationCategory.ADMIN,
    "COMMAND": OperationCategory.ADMIN,
    "FAILOVER": OperationCategory.ADMIN,
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


class RedisPermissionPolicy(CategoryBasedPermissionPolicy):
    """Permission policy for Redis.

    Maps the readonly/writer/admin roles to allowed Redis command
    categories. Dangerous commands (FLUSHALL, SHUTDOWN, etc.) are only
    allowed for the admin role.
    """

    _OPERATION_CATEGORIES = _COMMAND_CATEGORIES
    _DANGEROUS_COMMANDS = _DANGEROUS_COMMANDS
    _datasource_name = "Redis"
