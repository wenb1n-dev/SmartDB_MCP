"""Kafka connection pool implementation.

Implements the :class:`ConnectionPool` ABC for Kafka using
``kafka-python`` (the synchronous Kafka client). Provides a unified
interface for acquiring Kafka admin/consumer connections within the
SmartDB multi-paradigm gateway.

``KafkaAdminClient`` is thread-safe and manages connections internally.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

from connection.base import ConnectionPool

logger = logging.getLogger(__name__)


class KafkaConnectionPool(ConnectionPool):
    """Kafka connection pool backed by ``kafka-python``.

    Uses ``KafkaAdminClient`` for admin operations (topic management,
    consumer group queries). The admin client is thread-safe and
    maintains connections to all brokers.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9092,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        pool_size: int = 10,
        **kwargs,
    ):
        """Initialize the Kafka connection pool.

        Args:
            host: Kafka broker host.
            port: Kafka broker port (default: 9092).
            user: SASL username (optional if no auth).
            password: SASL password (optional if no auth).
            database: Not used for Kafka (kept for interface compatibility).
            pool_size: Metadata only (kafka-python manages connections internally).
        """
        from kafka import KafkaAdminClient

        self.host = host
        self.port = port
        self.bootstrap_servers = f"{host}:{port}"
        self.max_pool_size = pool_size

        # Build client config
        config = {
            "bootstrap_servers": self.bootstrap_servers,
            "request_timeout_ms": 30000,
            "api_version_auto_timeout_ms": 10000,
        }

        # SASL authentication
        if user and password:
            config["security_protocol"] = "SASL_PLAINTEXT"
            config["sasl_mechanism"] = "PLAIN"
            config["sasl_plain_username"] = user
            config["sasl_plain_password"] = password

        self._admin_client = KafkaAdminClient(**config)

        logger.info(
            f"Kafka connection pool initialized for {self.bootstrap_servers}"
        )

    def get_connection(self) -> Any:
        """Acquire the Kafka admin client instance.

        Returns the :class:`KafkaAdminClient` instance. The client is
        thread-safe and shared across all callers.
        """
        logger.debug("Kafka admin client acquired")
        return self._admin_client

    def return_connection(self, conn: Any) -> None:
        """Return a Kafka connection to the pool.

        ``kafka-python`` manages connections internally. This is a no-op
        wrapper to satisfy the :class:`ConnectionPool` interface.
        """
        logger.debug("Kafka connection returned to pool")

    @contextmanager
    def connection(self) -> Iterator[Any]:
        """Context manager for acquiring a Kafka admin client.

        Usage::

            with pool.connection() as admin:
                topics = admin.list_topics()
        """
        client = self.get_connection()
        try:
            yield client
        finally:
            self.return_connection(client)

    def get_stats(self) -> Dict[str, Any]:
        """Get Kafka connection pool statistics."""
        stats = {
            "pool_type": "kafka",
            "bootstrap_servers": self.bootstrap_servers,
            "max_pool_size": self.max_pool_size,
        }
        # Try to get broker info
        try:
            from kafka import KafkaConsumer
            consumer = KafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                request_timeout_ms=5000,
                api_version_auto_timeout_ms=3000,
            )
            brokers = consumer._client.cluster.brokers()
            stats["brokers"] = len(list(brokers))
            consumer.close(autocommit=False)
        except Exception:
            stats["brokers"] = "unavailable"
        return stats

    def close_all_connections(self) -> None:
        """Close all connections in the Kafka pool."""
        try:
            self._admin_client.close()
            logger.info("All Kafka connections closed")
        except Exception as e:
            logger.error(f"Error closing Kafka connections: {e}")
