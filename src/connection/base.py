"""Abstract base class for database connection pools.

This abstraction decouples the connection pool interface from SQLAlchemy,
allowing non-SQLAlchemy-based pools (Redis, MongoDB, etc.) to be integrated
under a unified interface.
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, Iterator


class ConnectionPool(ABC):
    """Abstract base class for all connection pool implementations.

    Subclasses must implement all abstract methods to provide a unified
    connection pool interface regardless of the underlying data source.
    """

    @abstractmethod
    def get_connection(self) -> Any:
        """Acquire a connection from the pool.

        Returns:
            A connection object specific to the underlying data source.
        """
        ...

    @abstractmethod
    def return_connection(self, conn: Any) -> None:
        """Return a connection to the pool.

        Args:
            conn: The connection object to return.
        """
        ...

    @abstractmethod
    @contextmanager
    def connection(self) -> Iterator[Any]:
        """Context manager for acquiring and automatically returning a connection.

        Usage:
            with pool.connection() as conn:
                result = conn.execute(...)
        """
        ...

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics.

        Returns:
            A dictionary containing pool statistics such as pool size,
            checked-out connections, available connections, etc.
        """
        ...

    @abstractmethod
    def close_all_connections(self) -> None:
        """Close all connections in the pool and release resources."""
        ...
