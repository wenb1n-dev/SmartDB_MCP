"""MongoDB connection pool implementation.

Implements the :class:`ConnectionPool` ABC for MongoDB using ``pymongo``
(the synchronous MongoDB driver). Provides a unified interface for acquiring
MongoDB client connections within the SmartDB multi-paradigm gateway.

``pymongo.MongoClient`` is thread-safe and manages a connection pool
internally with ``maxPoolSize`` and ``minPoolSize`` parameters.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from connection.base import ConnectionPool

logger = logging.getLogger(__name__)


class MongoDBConnectionPool(ConnectionPool):
    """MongoDB connection pool backed by ``pymongo``.

    Uses ``pymongo.MongoClient`` which is thread-safe and manages
    connections internally via a built-in connection pool.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 27017,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        auth_source: str = "admin",
        max_pool_size: int = 50,
        min_pool_size: int = 5,
        server_selection_timeout: int = 5,
        socket_timeout: int = 5,
        **kwargs,
    ):
        """Initialize the MongoDB connection pool.

        Args:
            host: MongoDB server host.
            port: MongoDB server port.
            user: MongoDB username (optional if no auth).
            password: MongoDB password (optional if no auth).
            database: Default database name (used for auth and as default).
            auth_source: Authentication database (default ``admin``).
            max_pool_size: Maximum number of connections in the pool.
            min_pool_size: Minimum number of connections to maintain.
            server_selection_timeout: Server selection timeout in seconds.
            socket_timeout: Socket timeout in seconds.
        """
        self.host = host
        self.port = port
        self.database = database
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size

        # Build MongoDB URI
        if user and password:
            uri = (
                f"mongodb://{user}:{password}@{host}:{port}"
                f"/{database or ''}?authSource={auth_source}"
            )
        else:
            uri = f"mongodb://{host}:{port}/{database or ''}"

        self._client = MongoClient(
            uri,
            maxPoolSize=max_pool_size,
            minPoolSize=min_pool_size,
            serverSelectionTimeoutMS=server_selection_timeout * 1000,
            socketTimeoutMS=socket_timeout * 1000,
        )

        logger.info(
            f"MongoDB connection pool initialized for {host}:{port}"
            f" database={database} max_pool_size={max_pool_size}"
        )

    def get_connection(self) -> MongoClient:
        """Acquire a MongoDB client from the pool.

        Returns the :class:`MongoClient` instance. The client is
        thread-safe and manages connections internally, so the same
        instance is returned on every call.
        """
        logger.debug("MongoDB client acquired")
        return self._client

    def return_connection(self, conn: Any) -> None:
        """Return a MongoDB connection to the pool.

        ``pymongo`` manages connection return internally via its
        built-in connection pool. This is a no-op wrapper to satisfy
        the :class:`ConnectionPool` interface.
        """
        logger.debug("MongoDB connection returned to pool")

    @contextmanager
    def connection(self) -> Iterator[MongoClient]:
        """Context manager for acquiring a MongoDB client.

        Usage::

            with pool.connection() as client:
                db = client["mydb"]
                collection = db["mycollection"]
        """
        client = self.get_connection()
        try:
            yield client
        finally:
            self.return_connection(client)

    def get_stats(self) -> Dict[str, Any]:
        """Get MongoDB connection pool statistics."""
        stats = {
            "pool_type": "mongodb",
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "max_pool_size": self.max_pool_size,
            "min_pool_size": self.min_pool_size,
        }
        # pymongo doesn't expose in-use/available counts directly
        try:
            server_info = self._client.server_info(timeoutMS=1000)
            stats["server_version"] = server_info.get("version", "unknown")
        except Exception:
            stats["server_version"] = "unavailable"
        return stats

    def close_all_connections(self) -> None:
        """Close all connections in the MongoDB pool."""
        try:
            self._client.close()
            logger.info("All MongoDB connections closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connections: {e}")
