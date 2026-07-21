"""KV store data source abstraction.

Defines the :class:`KVStoreFactory` ABC for key-value data sources.
Unlike relational databases, KV stores have their own operation set:
command execution, key info querying, and key scanning.

Common operations (db_version, db_health) are inherited from
:class:`DataSourceFactory`.
"""

from abc import abstractmethod
from typing import ClassVar

from datasource.base import DataSourceFactory, Paradigm


class KVStoreFactory(DataSourceFactory):
    """Abstract base class for key-value data source factories.

    Subclasses (e.g., ``RedisFactory``) implement the KV-specific
    abstract methods defined here. The ``paradigm`` is set to
    ``Paradigm.KV_STORE``.
    """

    paradigm: ClassVar[Paradigm] = Paradigm.KV_STORE

    @abstractmethod
    def create_command_executor(self):
        """Create a command executor handler.

        Returns a handler that can execute raw KV commands (e.g.,
        Redis GET/SET/HGET/LPUSH).
        """
        ...

    @abstractmethod
    def create_key_info(self):
        """Create a key info handler.

        Returns a handler that can query key metadata: type, size,
        TTL, etc.
        """
        ...

    @abstractmethod
    def create_key_scanner(self):
        """Create a key scanner handler.

        Returns a handler that can scan keys by pattern.
        """
        ...
