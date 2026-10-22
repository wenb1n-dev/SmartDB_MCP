"""Message queue data source abstraction.

Defines the :class:`MessageQueueFactory` ABC for message queue data sources.
Message queues have their own operation set: topic listing, topic info
querying, and consumer lag querying.

Common operations (db_version, db_health) are inherited from
:class:`DataSourceFactory`.
"""

from abc import abstractmethod
from typing import ClassVar

from datasource.base import DataSourceFactory, Paradigm


class MessageQueueFactory(DataSourceFactory):
    """Abstract base class for message queue data source factories.

    Subclasses (e.g., ``KafkaFactory``) implement the message-queue-specific
    abstract methods defined here. The ``paradigm`` is set to
    ``Paradigm.MESSAGE_QUEUE``.
    """

    paradigm: ClassVar[Paradigm] = Paradigm.MESSAGE_QUEUE

    @abstractmethod
    def create_topic_lister(self):
        """Create a topic lister handler.

        Returns a handler that can list topics in the cluster, with
        optional filtering.
        """
        ...

    @abstractmethod
    def create_topic_info(self):
        """Create a topic info handler.

        Returns a handler that can query topic metadata: partitions,
        leaders, replicas, ISR, configs.
        """
        ...

    @abstractmethod
    def create_consumer_lag(self):
        """Create a consumer lag handler.

        Returns a handler that can query consumer group lag: group
        offsets, topic partition offsets, lag per partition.
        """
        ...
