"""
SQLAlchemy数据库连接池工具类
支持多种数据库类型，提供统一的连接池管理接口
"""

import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, SingletonThreadPool, NullPool
from sqlalchemy.exc import SQLAlchemyError

# 配置日志
logger = logging.getLogger(__name__)


class SQLAlchemyConnectionPool:
    """
    基于SQLAlchemy的数据库连接池实现
    """

    def __init__(self, database_url: str, 
                 pool_type: str = "queue",
                 pool_size: int = 10,
                 max_overflow: int = 20,
                 pool_recycle: int = 3600,
                 pool_pre_ping: bool = True,
                 pool_timeout: int = 30,
                 **kwargs):
        """
        初始化连接池
        
        Args:
            database_url: 数据库连接URL
            pool_type: 连接池类型 ('queue', 'singleton', 'null')
            pool_size: 连接池大小
            max_overflow: 超出pool_size后最多可创建的连接数
            pool_recycle: 连接回收时间(秒)，-1表示不回收
            pool_pre_ping: 是否在使用前ping数据库以检查连接有效性
            pool_timeout: 获取连接的超时时间(秒)
            **kwargs: 其他传递给create_engine的参数
        """
        self.database_url = database_url
        self.pool_type = pool_type
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self.pool_timeout = pool_timeout
        
        # 创建引擎
        self.engine = self._create_engine(**kwargs)
        
        logger.info(f"SQLAlchemy connection pool initialized for {database_url}")
        logger.info(f"Pool type: {pool_type}, Pool size: {pool_size}, Max overflow: {max_overflow}")

    def _create_engine(self, **kwargs) -> Engine:
        """
        创建SQLAlchemy引擎
        
        Returns:
            Engine: SQLAlchemy引擎实例
        """
        # 根据类型选择连接池
        pool_class_map = {
            'queue': QueuePool,
            'singleton': SingletonThreadPool,
            'null': NullPool
        }
        
        pool_class = pool_class_map.get(self.pool_type, QueuePool)
        
        # 创建引擎
        engine = create_engine(
            self.database_url,
            poolclass=pool_class,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=self.pool_pre_ping,
            pool_timeout=self.pool_timeout,
            **kwargs
        )

        return engine

    def get_connection(self):
        """
        获取数据库连接
        
        Returns:
            数据库连接对象
        """
        try:
            conn = self.engine.connect()
            logger.debug("Database connection acquired from pool")
            return conn
        except SQLAlchemyError as e:
            logger.error(f"Failed to acquire database connection: {e}")
            raise

    def return_connection(self, conn):
        """
        归还数据库连接到连接池
        
        Args:
            conn: 数据库连接对象
        """
        try:
            conn.close()
            logger.debug("Database connection returned to pool")
        except SQLAlchemyError as e:
            logger.warning(f"Error returning connection to pool: {e}")

    @contextmanager
    def connection(self):
        """
        上下文管理器方式使用连接
        
        Usage:
            with pool.connection() as conn:
                # 使用连接执行数据库操作
                result = conn.execute(text("SELECT 1"))
        """
        conn = self.get_connection()
        try:
            yield conn
        finally:
            self.return_connection(conn)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取连接池统计信息
        
        Returns:
            包含连接池统计信息的字典
        """
        pool = self.engine.pool
        return {
            "pool_type": self.pool_type,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "checked_out_connections": pool.checkedout(),
            "available_connections": pool.checkedin(),
            "overflow_connections": getattr(pool, 'overflow', 0),
            "recycle_time": self.pool_recycle
        }

    def close_all_connections(self):
        """
        关闭所有连接
        """
        try:
            self.engine.dispose()
            logger.info("All database connections closed")
        except Exception as e:
            logger.error(f"Error closing all connections: {e}")


