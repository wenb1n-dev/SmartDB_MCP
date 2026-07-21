from abc import ABC, abstractmethod
from typing import Dict, Any, Type
from urllib.parse import quote_plus

from connection.base import ConnectionPool
from connection.connection_pool import SQLAlchemyConnectionPool
from connection.redis_pool import RedisConnectionPool
from connection.mongodb_pool import MongoDBConnectionPool


class DatabasePoolCreator(ABC):
    """数据库连接池创建器抽象基类

    Each concrete creator produces a :class:`ConnectionPool` instance for a
    specific database type. New creators can be registered at runtime via
    :meth:`DatabasePoolFactory.register_creator`.
    """

    @abstractmethod
    def create_pool(self, pool_name: str, config: Dict[str, Any]) -> ConnectionPool:
        """Create a connection pool for the given database configuration."""
        pass


class MySQLPoolCreator(DatabasePoolCreator):
    """MySQL连接池创建器"""

    def create_pool(self, pool_name: str, config: Dict[str, Any]) -> ConnectionPool:
        user = quote_plus(config['user'])
        password = quote_plus(config['password'])
        database_url = f"mysql+pymysql://{user}:{password}@{config['host']}:{config['port']}/{config['database']}"
        return SQLAlchemyConnectionPool(
            database_url=database_url,
            pool_type=config.get("pool_type", "queue"),
            pool_size=config.get("pool_size", 10),
            max_overflow=config.get("max_overflow", 20),
            pool_recycle=config.get("pool_recycle", 3600),
            pool_timeout=config.get("pool_timeout", 30)
        )


class PostgreSQLPoolCreator(DatabasePoolCreator):
    """PostgreSQL连接池创建器"""

    def create_pool(self, pool_name: str, config: Dict[str, Any]) -> ConnectionPool:
        user = quote_plus(config['user'])
        password = quote_plus(config['password'])
        database_url = f"postgresql+psycopg2://{user}:{password}@{config['host']}:{config['port']}/{config['database']}"
        schema = config.get("schema", "public")
        return SQLAlchemyConnectionPool(
            database_url=database_url,
            pool_type=config.get("pool_type", "queue"),
            pool_size=config.get("pool_size", 10),
            max_overflow=config.get("max_overflow", 20),
            pool_recycle=config.get("pool_recycle", 3600),
            pool_timeout=config.get("pool_timeout", 30),
            connect_args={"options": f"-csearch_path={schema}"}
        )


class OraclePoolCreator(DatabasePoolCreator):
    def create_pool(self, pool_name: str, config: Dict[str, Any]) -> ConnectionPool:
        user = quote_plus(config['user'])
        password = quote_plus(config['password'])
        service_name = config.get("service_name", "ORCL")
        database_url = f"oracle+oracledb://{user}:{password}@{config['host']}:{config['port']}/{service_name}"
        return SQLAlchemyConnectionPool(
            database_url=database_url,
            pool_type=config.get("pool_type", "queue"),
            pool_size=config.get("pool_size", 10),
            max_overflow=config.get("max_overflow", 20),
            pool_recycle=config.get("pool_recycle", 3600),
            pool_timeout=config.get("pool_timeout", 30)
        )


class MSSQLServerPoolCreator(DatabasePoolCreator):
    """MSSQL数据库连接池创建器"""
    def create_pool(self, pool_name: str, config: Dict[str, Any]) -> ConnectionPool:
        user = quote_plus(config['user'])
        password = quote_plus(config['password'])
        database_url = f"mssql+pymssql://{user}:{password}@{config['host']}:{config['port']}/{config['database']}"
        return SQLAlchemyConnectionPool(
            database_url=database_url,
            pool_type=config.get("pool_type", "queue"),
            pool_size=config.get("pool_size", 10),
            max_overflow=config.get("max_overflow", 20),
            pool_recycle=config.get("pool_recycle", 3600),
            pool_timeout=config.get("pool_timeout", 30)
        )


class DamengPoolCreator(DatabasePoolCreator):
    """达梦数据库连接池创建器"""
    def create_pool(self, pool_name: str, config: Dict[str, Any]) -> ConnectionPool:
        user = quote_plus(config['user'])
        password = quote_plus(config['password'])
        database_url = f"dm+dmPython://{user}:{password}@{config['host']}:{config['port']}"

        # 获取schema配置，如果存在则通过connect_args传递
        connect_args = {}
        if 'schema' in config:
            connect_args['schema'] = config['schema']

        return SQLAlchemyConnectionPool(
            database_url=database_url,
            pool_type=config.get("pool_type", "queue"),
            pool_size=config.get("pool_size", 10),
            max_overflow=config.get("max_overflow", 20),
            pool_recycle=config.get("pool_recycle", 3600),
            pool_timeout=config.get("pool_timeout", 30),
            connect_args=connect_args
        )


class RedisPoolCreator(DatabasePoolCreator):
    """Redis 连接池创建器"""
    def create_pool(self, pool_name: str, config: Dict[str, Any]) -> ConnectionPool:
        return RedisConnectionPool(
            host=config.get("host", "127.0.0.1"),
            port=int(config.get("port", 6379)),
            password=config.get("password"),
            db=int(config.get("db", 0)),
            max_connections=int(config.get("pool_size", 50)),
            socket_timeout=int(config.get("socket_timeout", 5)),
            socket_connect_timeout=int(config.get("pool_timeout", 5)),
        )


class MongoDBPoolCreator(DatabasePoolCreator):
    """MongoDB 连接池创建器"""
    def create_pool(self, pool_name: str, config: Dict[str, Any]) -> ConnectionPool:
        return MongoDBConnectionPool(
            host=config.get("host", "127.0.0.1"),
            port=int(config.get("port", 27017)),
            user=config.get("user"),
            password=config.get("password"),
            database=config.get("database"),
            auth_source=config.get("auth_source", "admin"),
            max_pool_size=int(config.get("pool_size", 50)),
            min_pool_size=int(config.get("min_pool_size", 5)),
            server_selection_timeout=int(config.get("pool_timeout", 5)),
            socket_timeout=int(config.get("socket_timeout", 5)),
        )


class DatabasePoolFactory:
    """数据库连接池工厂类

    Supports runtime registration of new pool creators for non-relational
    data sources (Redis, MongoDB, etc.) via :meth:`register_creator`.
    """

    _creators: Dict[str, DatabasePoolCreator] = {
        "mysql": MySQLPoolCreator(),
        "postgresql": PostgreSQLPoolCreator(),
        "oracle": OraclePoolCreator(),
        "mssqlserver": MSSQLServerPoolCreator(),
        "dameng": DamengPoolCreator(),
        "redis": RedisPoolCreator(),
        "mongodb": MongoDBPoolCreator(),
    }

    @classmethod
    def register_creator(cls, db_type: str, creator: DatabasePoolCreator) -> None:
        """Register a new pool creator for a database type.

        Allows extending the factory with new data source types (e.g.,
        ``"redis"``) without modifying this module.
        """
        cls._creators[db_type.lower()] = creator

    @classmethod
    def create_pool(cls, db_type: str, pool_name: str, config: Dict[str, Any]) -> ConnectionPool:
        """创建数据库连接池"""
        creator = cls._creators.get(db_type.lower())
        if not creator:
            raise ValueError(f"Unsupported database type: {db_type}")
        return creator.create_pool(pool_name, config)