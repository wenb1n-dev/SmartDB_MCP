"""Factory registry for data source factories.

Provides a global registry that maps data source type names (e.g. ``"mysql"``,
``"redis"``) to their corresponding factory classes. Factories are registered
as classes and lazily instantiated on first lookup.

This module is the canonical location for ``FactoryRegistry``. It was moved
here from ``databases/database_factory.py`` to eliminate the reverse
dependency from ``datasource`` (top-level abstraction) back to ``databases``
(relational implementation).

Registration flow:
1. ``DataSourceFactory.__init_subclass__`` appends each concrete factory
   class to ``FactoryRegistry._pending``.
2. After all paradigm packages are imported, ``datasource/__init__.py``
   calls ``FactoryRegistry.register_pending()`` to register them all.
"""

import importlib.util
from typing import ClassVar, Dict, List, Type

from config.dbconfig import get_db_config_by_name


class FactoryRegistry:
    """Global registry for data source factory classes.

    Stores factory classes keyed by their ``name`` attribute. Instances are
    created lazily on first access and cached as singletons.

    Lookup can be performed by factory name (e.g. ``"mysql"``) or by
    connection pool name (which is resolved to a factory name via
    ``get_db_config_by_name``).
    """

    # Factory classes indexed by name (e.g. "mysql", "redis")
    _factory_classes: ClassVar[Dict[str, Type]] = {}
    # Cached singleton instances
    _instances: ClassVar[Dict[str, object]] = {}
    # Pending factory classes collected by __init_subclass__, awaiting
    # batch registration via register_pending().
    _pending: ClassVar[List[Type]] = []

    @classmethod
    def add_pending(cls, factory_class: Type) -> None:
        """Add a factory class to the pending registration queue.

        Called by ``DataSourceFactory.__init_subclass__`` for every
        concrete factory subclass with a non-empty ``name``.

        Args:
            factory_class: A ``DataSourceFactory`` subclass.
        """
        cls._pending.append(factory_class)

    @classmethod
    def register_pending(cls) -> None:
        """Register all pending factory classes and clear the queue.

        Called once after all paradigm packages have been imported.
        """
        for factory_cls in cls._pending:
            cls.register(factory_cls)
        cls._pending.clear()

    @classmethod
    def register(cls, factory_class: Type) -> Type:
        """Register a factory class.

        Only the class is stored; instantiation is deferred to first lookup.

        Args:
            factory_class: A ``DataSourceFactory`` subclass with a non-empty
                ``name`` class attribute.

        Returns:
            The same factory class (allows use as a decorator).
        """
        cls._factory_classes[factory_class.name] = factory_class
        return factory_class

    @classmethod
    def get_factory_by_factory_name(cls, name: str):
        """Get a factory instance by its registered name.

        Lazily instantiates the factory on first access and caches it.

        Args:
            name: Factory name (e.g. ``"mysql"``, ``"redis"``).

        Returns:
            A ``DataSourceFactory`` instance.

        Raises:
            ValueError: When no factory is registered under ``name``.
        """
        if name not in cls._instances:
            if name not in cls._factory_classes:
                raise ValueError(f"工厂 {name} 未注册")
            cls._instances[name] = cls._factory_classes[name]()
        return cls._instances[name]

    @classmethod
    def get_factory_by_pool_name(cls, pool_name: str):
        """Get a factory instance by connection pool name.

        Resolves the pool name to a factory name via the database config,
        then delegates to :meth:`get_factory_by_factory_name`.

        Args:
            pool_name: Connection pool name as defined in
                ``database_config.json``.

        Returns:
            A ``DataSourceFactory`` instance.

        Raises:
            ValueError: When the pool's factory type is not registered.
        """
        db_config = get_db_config_by_name(pool_name)
        name = db_config.get("type")

        if name not in cls._instances:
            if name not in cls._factory_classes:
                raise ValueError(f"工厂 {name} 未注册")
            cls._instances[name] = cls._factory_classes[name]()
        return cls._instances[name]
