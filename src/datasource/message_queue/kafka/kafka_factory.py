"""Kafka factory implementation.

Registers with FactoryRegistry and provides handlers for all message queue
operations: topic listing, consumer lag querying, version query, and health check.
"""

from datasource.base import Paradigm
from datasource.message_queue.base import MessageQueueFactory
from datasource.message_queue.kafka.kafka_consumer_groups import KafkaConsumerGroups
from datasource.message_queue.kafka.kafka_db_version import KafkaDatabaseVersion
from datasource.message_queue.kafka.kafka_health import KafkaHealth
from datasource.message_queue.kafka.kafka_topics import KafkaTopics
from permission.kafka_permission import KafkaPermissionPolicy


class KafkaFactory(MessageQueueFactory):
    """Factory for Kafka data source operations.

    This factory is registered with ``FactoryRegistry`` under the name
    ``"kafka"``. It creates handlers for topic listing, consumer lag
    querying, version query, and health check.
    """

    name: str = "kafka"
    paradigm = Paradigm.MESSAGE_QUEUE

    def create_db_version(self) -> KafkaDatabaseVersion:
        return KafkaDatabaseVersion()

    def create_db_health(self) -> KafkaHealth:
        return KafkaHealth()

    def create_topic_lister(self) -> KafkaTopics:
        return KafkaTopics()

    def create_topic_info(self) -> KafkaTopics:
        # Reuse KafkaTopics for topic info queries
        return KafkaTopics()

    def create_consumer_lag(self) -> KafkaConsumerGroups:
        return KafkaConsumerGroups()

    def create_permission_policy(self) -> KafkaPermissionPolicy:
        return KafkaPermissionPolicy()
