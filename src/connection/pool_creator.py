from abc import ABC, abstractmethod
from typing import Dict, Any
from urllib.parse import quote_plus

from connection.connection_pool import SQLAlchemyConnectionPool

class DatabasePoolCreator(ABC):
    """数据库连接池创建器抽象基类"""
    @abstractmethod
    def create_pool(self, pool_name: str, config: Dict[str, Any]) -> SQLAlchemyConnectionPool:
        pass

class MySQLPoolCreator(DatabasePoolCreator):
    """MySQL连接池创建器"""

    def create_pool(self, pool_name: str, config: Dict[str, Any]) -> SQLAlchemyConnectionPool:
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

    def create_pool(self, pool_name: str, config: Dict[str, Any]) -> SQLAlchemyConnectionPool:
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
    def create_pool(self, pool_name: str, config: Dict[str, Any]) -> SQLAlchemyConnectionPool:
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
    def create_pool(self, pool_name: str, config: Dict[str, Any]) -> SQLAlchemyConnectionPool:
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

class DatabasePoolFactory:
    """数据库连接池工厂类"""

    _creators = {
        "mysql": MySQLPoolCreator(),
        "postgresql": PostgreSQLPoolCreator(),
        "oracle": OraclePoolCreator(),
        "mssqlserver": MSSQLServerPoolCreator()
    }
    @classmethod
    def create_pool(cls, db_type: str, pool_name: str, config: Dict[str, Any]) -> SQLAlchemyConnectionPool:
        """创建数据库连接池"""
        creator = cls._creators.get(db_type.lower())
        if not creator:
            raise ValueError(f"Unsupported database type: {db_type}")
        return creator.create_pool(pool_name, config)