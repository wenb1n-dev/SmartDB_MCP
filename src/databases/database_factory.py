from abc import ABC, abstractmethod
from typing import ClassVar, Dict, Type

from config.dbconfig import get_db_config_by_name
from databases.base.base import TableDescription, DatabaseVersion, TableName, TableIndex, DatabaseHealth


class FactoryRegistry:
    # 存储工厂类而不是工厂实例
    _factory_classes: ClassVar[Dict[str, Type['DatabaseOperationFactory']]] = {}
    # 存储已创建的工厂实例
    _instances: ClassVar[Dict[str, 'DatabaseOperationFactory']] = {}

    @classmethod
    def register(cls, factory_class: Type['DatabaseOperationFactory']) -> Type['DatabaseOperationFactory']:
        # 只注册类，不立即实例化
        factory = factory_class
        cls._factory_classes[factory.name] = factory
        return factory_class

    @classmethod
    def get_factory_by_factory_name(cls, name: str) -> 'DatabaseOperationFactory':
        # 延迟初始化：只有在需要时才创建实例
        if name not in cls._instances:
            if name not in cls._factory_classes:
                raise ValueError(f"工厂 {name} 未注册")
            cls._instances[name] = cls._factory_classes[name]()
        return cls._instances[name]

    @classmethod
    def get_factory_by_pool_name(cls, pool_name: str) -> 'DatabaseOperationFactory':
        db_config = get_db_config_by_name(pool_name)
        name = db_config.get("type")

        # 延迟初始化：只有在需要时才创建实例
        if name not in cls._instances:
            if name not in cls._factory_classes:
                raise ValueError(f"工厂 {name} 未注册")
            cls._instances[name] = cls._factory_classes[name]()
        return cls._instances[name]

class DatabaseOperationFactory(ABC):
    name: str = ""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.name:
            FactoryRegistry.register(cls)

    @abstractmethod
    def create_db_version(self) -> "DatabaseVersion":
        pass
    @abstractmethod
    def create_table_description(self) -> "TableDescription":
        pass
    @abstractmethod
    def create_table_name(self) -> "TableName":
        pass
    @abstractmethod
    def create_table_index(self) -> "TableIndex":
        pass
    @abstractmethod
    def create_db_health(self) -> "DatabaseHealth":
        pass

    @classmethod
    def get_factory_by_pool_name(cls, pool_name: str) -> 'DatabaseOperationFactory':
        return FactoryRegistry.get_factory_by_pool_name(pool_name)

