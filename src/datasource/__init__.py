"""Data source abstraction package.

This package provides the top-level abstraction for all data source types.
The DataSourceFactory and Paradigm are the main abstractions defined here.

FactoryRegistry and concrete factory classes are accessed via
databases.database_factory (for relational) or their respective
datasource subpackages (for other paradigms).
"""

from datasource.base import DataSourceFactory, Paradigm

__all__ = [
    "DataSourceFactory",
    "Paradigm",
]


def _register_redis_factory() -> None:
    """Register RedisFactory with FactoryRegistry.

    Called at import time. Uses a try/except so that the package still
    loads if the ``redis`` library is not installed.
    """
    try:
        from databases.database_factory import FactoryRegistry
        from datasource.kv.redis.redis_factory import RedisFactory
        FactoryRegistry.register(RedisFactory)
    except ImportError:
        pass


def _register_mongodb_factory() -> None:
    """Register MongoDBFactory with FactoryRegistry.

    Called at import time. Uses a try/except so that the package still
    loads if the ``pymongo`` library is not installed.
    """
    try:
        from databases.database_factory import FactoryRegistry
        from datasource.document.mongodb.mongodb_factory import MongoDBFactory
        FactoryRegistry.register(MongoDBFactory)
    except ImportError:
        pass


_register_redis_factory()
_register_mongodb_factory()
