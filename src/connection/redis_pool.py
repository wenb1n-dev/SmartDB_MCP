"""Redis connection pool implementation.

Implements the :class:`ConnectionPool` ABC for Redis using ``redis-py``'s
built-in :class:`redis.ConnectionPool`. Provides a unified interface for
acquiring Redis connections within the SmartDB multi-paradigm gateway.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

from redis import Redis
from redis.connection import ConnectionPool as RedisPyConnectionPool
from redis.exceptions import RedisError

from connection.base import ConnectionPool

logger = logging.getLogger(__name__)


class RedisConnectionPool(ConnectionPool):
    """Redis connection pool backed by ``redis-py``.

    Unlike SQLAlchemy pools, Redis connections are lightweight and the
    underlying ``redis.ConnectionPool`` manages connection reuse internally.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        max_connections: int = 50,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        **kwargs,
    ):
        """Initialize the Redis connection pool.

        Args:
            host: Redis server host.
            port: Redis server port.
            password: Redis password (if any).
            db: Redis database index.
            max_connections: Maximum number of connections in the pool.
            socket_timeout: Socket timeout in seconds.
            socket_connect_timeout: Connection establishment timeout.
        """
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout

        self._pool = RedisPyConnectionPool(
            host=host,
            port=port,
            password=password,
            db=db,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            decode_responses=True,
        )

        logger.info(
            f"Redis connection pool initialized for {host}:{port} db={db} "
            f"max_connections={max_connections}"
        )

    def get_connection(self) -> Redis:
        """Acquire a Redis client from the pool.

        Returns a :class:`redis.Redis` instance bound to the underlying
        connection pool. The connection is automatically returned when
        the client is garbage-collected or explicitly closed.
        """
        try:
            client = Redis(connection_pool=self._pool)
            logger.debug("Redis connection acquired from pool")
            return client
        except RedisError as e:
            logger.error(f"Failed to acquire Redis connection: {e}")
            raise

    def return_connection(self, conn: Any) -> None:
        """Return a Redis connection to the pool.

        ``redis-py`` manages connection return internally via the
        connection pool's ``release`` method. This is a no-op wrapper
        to satisfy the :class:`ConnectionPool` interface.
        """
        try:
            if hasattr(conn, "close"):
                conn.close()
            logger.debug("Redis connection returned to pool")
        except RedisError as e:
            logger.warning(f"Error returning Redis connection to pool: {e}")

    @contextmanager
    def connection(self) -> Iterator[Redis]:
        """Context manager for acquiring a Redis client.

        Usage::

            with pool.connection() as client:
                client.set("key", "value")
                value = client.get("key")
        """
        client = self.get_connection()
        try:
            yield client
        finally:
            self.return_connection(client)

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis connection pool statistics."""
        return {
            "pool_type": "redis",
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "max_connections": self.max_connections,
            "in_use_connections": self._pool._in_use_connections,
            "available_connections": len(self._pool._available_connections),
        }

    def close_all_connections(self) -> None:
        """Close all connections in the Redis pool."""
        try:
            self._pool.disconnect()
            logger.info("All Redis connections closed")
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")
