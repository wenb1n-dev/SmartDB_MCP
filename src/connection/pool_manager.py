"""
多数据库连接池管理器示例
展示如何使用SQLAlchemyConnectionPool管理多个数据库连接池
"""

import logging
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
import threading

from .connection_pool import (
    SQLAlchemyConnectionPool
)
from config.dbconfig import get_db_configs
from .pool_creator import DatabasePoolFactory

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
        """ 创建连接池 """
        pool = DatabasePoolFactory.create_pool(db_type=config["type"], pool_name=pool_name, config=config)
        self._pools[pool_name] = pool

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


