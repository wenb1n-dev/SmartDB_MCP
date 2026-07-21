"""Milvus connection pool implementation.

Implements the :class:`ConnectionPool` ABC for Milvus using ``pymilvus``
(the official synchronous Milvus Python SDK). Provides a unified interface
for acquiring Milvus connections within the SmartDB multi-paradigm gateway.

``pymilvus.MilvusClient`` is thread-safe and manages connections internally.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

from connection.base import ConnectionPool

logger = logging.getLogger(__name__)


class MilvusConnectionPool(ConnectionPool):
    """Milvus connection pool backed by ``pymilvus``.

    Uses ``pymilvus.MilvusClient`` which is thread-safe and manages
    a single gRPC channel to the Milvus server. For high-concurrency
    scenarios, multiple pool instances can be created.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 19530,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        token: Optional[str] = None,
        pool_size: int = 10,
        **kwargs,
    ):
        """Initialize the Milvus connection pool.

        Args:
            host: Milvus server host.
            port: Milvus server port (default: 19530).
            user: Milvus username (optional if no auth).
            password: Milvus password (optional if no auth).
            database: Milvus database name (default: "default").
            token: Authentication token (alternative to user/password).
            pool_size: Maximum number of connections (used for metadata only,
                       pymilvus manages gRPC channels internally).
        """
        from pymilvus import MilvusClient

        self.host = host
        self.port = port
        self.database = database or "default"
        self.max_pool_size = pool_size

        uri = f"http://{host}:{port}"

        # Build client kwargs
        client_kwargs = {
            "uri": uri,
            "db_name": self.database,
        }
        if token:
            client_kwargs["token"] = token
        elif user and password:
            client_kwargs["token"] = f"{user}:{password}"

        self._client = MilvusClient(**client_kwargs)

        logger.info(
            f"Milvus connection pool initialized for {host}:{port}"
            f" database={self.database}"
        )

    def get_connection(self) -> Any:
        """Acquire a Milvus client instance.

        Returns the :class:`MilvusClient` instance. The client is
        thread-safe and shared across all callers.
        """
        logger.debug("Milvus client acquired")
        return self._client

    def return_connection(self, conn: Any) -> None:
        """Return a Milvus connection to the pool.

        ``pymilvus`` manages connections internally via gRPC channels.
        This is a no-op wrapper to satisfy the :class:`ConnectionPool`
        interface.
        """
        logger.debug("Milvus connection returned to pool")

    @contextmanager
    def connection(self) -> Iterator[Any]:
        """Context manager for acquiring a Milvus client.

        Usage::

            with pool.connection() as client:
                client.list_collections()
        """
        client = self.get_connection()
        try:
            yield client
        finally:
            self.return_connection(client)

    def get_stats(self) -> Dict[str, Any]:
        """Get Milvus connection pool statistics."""
        stats = {
            "pool_type": "milvus",
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "max_pool_size": self.max_pool_size,
        }
        # Try to get server version for additional info
        try:
            version = self._client.get_server_version()
            stats["server_version"] = version
        except Exception:
            stats["server_version"] = "unavailable"
        return stats

    def close_all_connections(self) -> None:
        """Close all connections in the Milvus pool."""
        try:
            self._client.close()
            logger.info("All Milvus connections closed")
        except Exception as e:
            logger.error(f"Error closing Milvus connections: {e}")
