"""KV data source paradigm package.

Defines the KVStoreFactory ABC and imports concrete KV implementations
(e.g., Redis) when their driver libraries are available.
"""

import importlib.util

from datasource.kv.base import KVStoreFactory

__all__ = ["KVStoreFactory"]

# Import concrete implementations only if their driver library is installed.
# Using find_spec() ensures that code errors in the factory module itself
# are NOT silently swallowed - only missing driver libraries are skipped.
if importlib.util.find_spec("redis"):
    from datasource.kv.redis.redis_factory import RedisFactory  # noqa: F401
    __all__.append("RedisFactory")
