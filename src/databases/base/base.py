from abc import ABC, abstractmethod
from typing import List, Dict, Any


class DatabaseVersion(ABC):
    @abstractmethod
    def get_db_version(self, pool_name: str) -> str:
        pass

class TableDescription(ABC):
    """
    表描述信息接口
    """

    @abstractmethod
    def get_table_description(self, pool_name: str, database: str, schema: str, table_name: str) -> str:
        """
        获取表描述信息

        Args:
            pool_name: 数据库名称
            table_name: 表名称

        Returns:
            表描述信息
        """
        pass

class TableName(ABC):
    """
    表名称接口
    """

    @abstractmethod
    def get_table_name(self, pool_name: str,  database: str, schema: str, text: str) -> str:
        """
        获取表名称

        Args:
            pool_name: 数据库名称
            text: 表描述

        Returns:
            表名称
        """

class TableIndex(ABC):
    """
    表索引接口
    """

    @abstractmethod
    def get_table_index(self, pool_name: str, database: str, schema: str, table_name: str) -> str:
        """
        获取表索引

        Args:
            pool_name: 数据库名称
            table_name: 表名称
        """
class DatabaseHealth(ABC):
    """
    数据库健康接口
    """
    @abstractmethod
    def get_db_health(self, pool_name: str, health_type: str):
        """
        获取数据库健康状态

        Args:
            pool_name: 数据库名称
            health_type: 健康类型
        """
