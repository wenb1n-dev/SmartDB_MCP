"""Redis factory implementation.

Registers with FactoryRegistry and provides handlers for all KV
operations: command execution, key info, key scanning, version query,
and health check.
"""

from datasource.base import Paradigm
from datasource.kv.base import KVStoreFactory
from datasource.kv.redis.redis_commands import RedisCommandExecutor
from datasource.kv.redis.redis_db_version import RedisDatabaseVersion
from datasource.kv.redis.redis_health import RedisHealth
from datasource.kv.redis.redis_key_info import RedisKeyInfo
from datasource.kv.redis.redis_scan import RedisKeyScanner
from permission.redis_permission import RedisPermissionPolicy


class RedisFactory(KVStoreFactory):
    """Factory for Redis data source operations.

    This factory is registered with ``FactoryRegistry`` under the name
    ``"redis"``. It creates handlers for command execution, key info
    querying, key scanning, version query, and health check.
    """

    name: str = "redis"
    paradigm = Paradigm.KV_STORE

    def create_db_version(self) -> RedisDatabaseVersion:
        return RedisDatabaseVersion()

    def create_db_health(self) -> RedisHealth:
        return RedisHealth()

    def create_command_executor(self) -> RedisCommandExecutor:
        return RedisCommandExecutor()

    def create_key_info(self) -> RedisKeyInfo:
        return RedisKeyInfo()

    def create_key_scanner(self) -> RedisKeyScanner:
        return RedisKeyScanner()

    def create_permission_policy(self) -> RedisPermissionPolicy:
        return RedisPermissionPolicy()
