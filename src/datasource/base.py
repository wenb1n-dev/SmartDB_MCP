"""Top-level data source abstraction layer.

Defines the Paradigm enum and DataSourceFactory abstract base class that
all data source factories (relational, KV, document, vector, etc.) inherit from.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import ClassVar, Dict, Type


class Paradigm(Enum):
    """Enumeration of data source paradigms.

    Each paradigm defines a distinct category of data source with its own
    tool set and operation semantics.
    """
    RELATIONAL = "relational"
    KV_STORE = "kv_store"
    DOCUMENT = "document"
    VECTOR = "vector"
    SEARCH_ENGINE = "search_engine"
    MESSAGE_QUEUE = "message_queue"


class DataSourceFactory(ABC):
    """Abstract base class for all data source factories.

    Every data source type (MySQL, Redis, MongoDB, etc.) must have a
    corresponding factory that inherits from this class. The factory
    declares its paradigm and provides methods to create operation handlers.

    Common operations (db_version, db_health) are defined here as they
    apply to all paradigms. Paradigm-specific operations are defined in
    subclasses (e.g., DatabaseOperationFactory for relational databases).
    """

    name: str = ""
    paradigm: ClassVar[Paradigm] = Paradigm.RELATIONAL

    @classmethod
    def get_paradigm(cls) -> Paradigm:
        """Get the paradigm of this data source factory."""
        return cls.paradigm

    @abstractmethod
    def create_db_version(self):
        """Create a database version handler.

        All paradigms support version querying, though the implementation
        differs (SQL VERSION() for relational, INFO for Redis, etc.).
        """
        ...

    @abstractmethod
    def create_db_health(self):
        """Create a database health check handler.

        All paradigms support health checking, though the metrics and
        diagnostic commands differ by data source type.
        """
        ...

    def create_permission_policy(self):
        """Create a permission policy for this data source.

        Subclasses should override this to provide paradigm-specific
        permission checking. The default implementation raises
        ``NotImplementedError`` for paradigms that do not yet define
        a permission policy.

        Returns:
            A :class:`PermissionPolicy` instance.
        """
        raise NotImplementedError(
            f"Permission policy not implemented for data source '{self.name}'"
        )
