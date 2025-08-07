"""
多数据库连接池管理器示例
展示如何使用SQLAlchemyConnectionPool管理多个数据库连接池
"""

import logging
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
import threading

from .SQLAlchemyConnectionPool import (
    SQLAlchemyConnectionPool
)
from src.config.dbconfig import get_db_configs

logger = logging.getLogger(__name__)


class MultiDBPoolManager:
    """
    多数据库连接池管理器
    管理多个不同数据库的连接池，提供统一的访问接口
    """
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "MultiDBPoolManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(auto_init_from_config=False)
        return cls._instance

    @classmethod
    def init_from_config(cls):
        """类方法：初始化单例并从配置加载所有连接池（只应在服务启动时调用一次）"""
        instance = cls.get_instance()
        instance._init_from_config()
        return instance

    @classmethod
    def get_pool(cls, pool_name: str) -> Optional[SQLAlchemyConnectionPool]:
        """类方法：获取指定名称的连接池"""
        instance = cls.get_instance()
        return instance._pools.get(pool_name)

    @classmethod
    def get_pool_names(cls):
        instance = cls.get_instance()
        return instance._pools.keys()

    def __init__(self, auto_init_from_config: bool = True):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._pools: Dict[str, SQLAlchemyConnectionPool] = {}
        logger.info("MultiDBPoolManager initialized")
        self._initialized = True
        if auto_init_from_config:
            self._init_from_config()

    def _init_from_config(self):
        """从配置文件自动初始化所有数据库连接池"""
        try:
            db_configs = get_db_configs()
            for db_name, config in db_configs.items():
                try:
                    self.add_pool_from_config(db_name, config)
                    logger.info(f"Successfully initialized pool '{db_name}'")
                except Exception as e:
                    logger.error(f"Failed to initialize pool '{db_name}': {e}")
            logger.info(f"Successfully initialized {len(self._pools)} database pools from config")
        except Exception as e:
            logger.error(f"Failed to initialize pools from config: {e}")

    def add_pool_from_config(self, pool_name: str, config: Dict[str, Any]) -> None:
        """
        从配置字典添加数据库连接池

        Args:
            pool_name: 连接池名称
            config: 数据库配置字典
        """
        db_type = config.get("type", "mysql")  # 默认为mysql
        user = config["user"]
        password = config["password"]
        host = config["host"]
        port = config["port"]
        database = config["database"]
        pool_type = config.get("pool_type", "queue")
        pool_size = config.get("pool_size", 10)
        max_overflow = config.get("max_overflow", 20)
        pool_recycle = config.get("pool_recycle", 3600)
        pool_timeout = config.get("pool_timeout", 30)

        if db_type.lower() == "mysql":
            pool = self.add_mysql_pool(
                pool_name=pool_name,
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                pool_type=pool_type,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_recycle=pool_recycle,
                pool_timeout=pool_timeout
            )
        elif db_type.lower() == "postgresql":
            pool = self.add_postgresql_pool(
                pool_name=pool_name,
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                pool_type=pool_type,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_recycle=pool_recycle,
                pool_timeout=pool_timeout
            )
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        self._pools[pool_name] = pool
        logger.info(f"Added {db_type} pool '{pool_name}' for database '{database}'")

    def add_mysql_pool(self,
                       pool_name: str,
                       host: str,
                       port: int = 3306,
                       user: str = "root",
                       password: str = "",
                       database: str = "",
                       pool_type: str = "queue",
                       pool_size: int = 10,
                       max_overflow: int = 20,
                       pool_recycle: int = 3600,
                       pool_timeout: int = 30,
                       **kwargs) -> SQLAlchemyConnectionPool:
        """
        添加MySQL连接池

        Args:
            pool_name: 连接池名称
            host: 数据库主机
            port: 数据库端口
            user: 用户名
            password: 密码
            database: 数据库名
            pool_type: 连接池类型
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
            pool_recycle: 连接回收时间
            pool_timeout: 连接超时时间
            **kwargs: 其他参数

        Returns:
            SQLAlchemyConnectionPool: MySQL连接池实例
        """
        database_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

        return SQLAlchemyConnectionPool(
            database_url=database_url,
            pool_type=pool_type,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            pool_timeout=pool_timeout,
            **kwargs
        )

    def add_postgresql_pool(self,
                           pool_name: str,
                           host: str,
                           port: int = 5432,  # PostgreSQL默认端口
                           user: str = "postgres",
                           password: str = "",
                           database: str = "",
                           pool_type: str = "queue",
                           pool_size: int = 10,
                           max_overflow: int = 20,
                           pool_recycle: int = 3600,
                           pool_timeout: int = 30,
                           **kwargs) -> SQLAlchemyConnectionPool:
        """
        添加PostgreSQL连接池

        Args:
            pool_name: 连接池名称
            host: 数据库主机
            port: 数据库端口
            user: 用户名
            password: 密码
            database: 数据库名
            pool_type: 连接池类型
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
            pool_recycle: 连接回收时间
            pool_timeout: 连接超时时间
            **kwargs: 其他参数

        Returns:
            SQLAlchemyConnectionPool: PostgreSQL连接池实例
        """
        database_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

        return SQLAlchemyConnectionPool(
            database_url=database_url,
            pool_type=pool_type,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            pool_timeout=pool_timeout,
            **kwargs
        )

    def remove_pool(self, pool_name: str) -> bool:
        """
        移除连接池

        Args:
            pool_name: 连接池名称

        Returns:
            bool: 是否成功移除
        """
        if pool_name in self._pools:
            pool = self._pools.pop(pool_name)
            pool.close_all_connections()
            logger.info(f"Removed pool '{pool_name}'")
            return True
        return False

    @contextmanager
    def connection(self, pool_name: str):
        """
        获取指定连接池的数据库连接（上下文管理器）

        Args:
            pool_name: 连接池名称

        Usage:
            with manager.connection('my_mysql_db') as conn:
                result = conn.execute(text("SELECT 1"))
        """
        pool = self.get_pool(pool_name)
        if not pool:
            raise ValueError(f"Pool '{pool_name}' not found")

        with pool.connection() as conn:
            yield conn

    def execute_query(self, pool_name: str, query: str, params: Optional[Dict] = None):
        """
        在指定数据库上执行查询语句

        Args:
            pool_name: 连接池名称
            query: SQL查询语句
            params: 查询参数

        Returns:
            查询结果
        """
        pool = self.get_pool(pool_name)
        if not pool:
            raise ValueError(f"Pool '{pool_name}' not found")

        return pool.execute_query(query, params)

    def execute_non_query(self, pool_name: str, query: str, params: Optional[Dict] = None):
        """
        在指定数据库上执行非查询语句

        Args:
            pool_name: 连接池名称
            query: SQL语句
            params: 查询参数

        Returns:
            影响的行数
        """
        pool = self.get_pool(pool_name)
        if not pool:
            raise ValueError(f"Pool '{pool_name}' not found")

        return pool.execute_non_query(query, params)

    def get_stats(self, pool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定连接池的统计信息

        Args:
            pool_name: 连接池名称

        Returns:
            包含连接池统计信息的字典，如果连接池不存在返回None
        """
        pool = self.get_pool(pool_name)
        if not pool:
            return None

        stats = pool.get_stats()
        stats["pool_name"] = pool_name
        return stats

    def get_all_stats(self) -> List[Dict[str, Any]]:
        """
        获取所有连接池的统计信息

        Returns:
            所有连接池统计信息的列表
        """
        return [self.get_stats(name) for name in self._pools.keys()]

    def close_all(self):
        """
        关闭所有连接池
        """
        for name, pool in self._pools.items():
            try:
                pool.close_all_connections()
                logger.info(f"Closed all connections for pool '{name}'")
            except Exception as e:
                logger.error(f"Error closing connections for pool '{name}': {e}")

        self._pools.clear()
        logger.info("All pools closed and cleared")


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建多数据库连接池管理器（自动从配置初始化）
    manager = MultiDBPoolManager(auto_init_from_config=True)
    
    try:
        # 显示所有可用的连接池
        print(f"Available pools: {manager.get_pool_names()}")
        
        # 使用连接池执行查询
        for pool_name in manager.get_pool_names():
            try:
                # 方法1: 使用上下文管理器
                with manager.connection(pool_name) as conn:
                    result = conn.execute("SELECT VERSION() as version")
                    version = result.fetchone()
                    print(f"Pool '{pool_name}' version: {version['version']}")
            except Exception as e:
                print(f"Error executing query on pool '{pool_name}': {e}")
            
            try:
                # 方法2: 直接执行查询
                results = manager.execute_query(pool_name, "SELECT DATABASE() as db")
                print(f"Pool '{pool_name}' current database: {results[0]['db']}")
            except Exception as e:
                print(f"Error executing direct query on pool '{pool_name}': {e}")
        
        # 查看所有连接池状态
        print("\n=== Pool Statistics ===")
        for stats in manager.get_all_stats():
            if stats:  # 确保stats不为None
                print(f"Pool '{stats['pool_name']}':")
                print(f"  Type: {stats['pool_type']}")
                print(f"  Size: {stats['pool_size']}")
                print(f"  Checked out connections: {stats['checked_out_connections']}")
                print(f"  Available connections: {stats['available_connections']}")
        
    except Exception as e:
        print(f"Error in example: {e}")
    finally:
        # 关闭所有连接池
        manager.close_all()