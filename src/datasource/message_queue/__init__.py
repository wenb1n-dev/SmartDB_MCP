"""Message queue paradigm data source package.

Defines the MessageQueueFactory ABC and imports concrete message queue
implementations (e.g., Kafka) when their driver libraries are available.
"""

import importlib.util

from datasource.message_queue.base import MessageQueueFactory

__all__ = ["MessageQueueFactory"]

if importlib.util.find_spec("kafka"):
    from datasource.message_queue.kafka.kafka_factory import KafkaFactory  # noqa: F401
    __all__.append("KafkaFactory")
