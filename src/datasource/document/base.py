"""Document store data source abstraction.

Defines the :class:`DocumentFactory` ABC for document-oriented data sources.
Unlike relational databases, document stores have their own operation set:
collection listing, schema inference, document queries, and index inspection.

Common operations (db_version, db_health) are inherited from
:class:`DataSourceFactory`.
"""

from abc import abstractmethod
from typing import ClassVar

from datasource.base import DataSourceFactory, Paradigm


class DocumentFactory(DataSourceFactory):
    """Abstract base class for document data source factories.

    Subclasses (e.g., ``MongoDBFactory``) implement the document-specific
    abstract methods defined here. The ``paradigm`` is set to
    ``Paradigm.DOCUMENT``.
    """

    paradigm: ClassVar[Paradigm] = Paradigm.DOCUMENT

    @abstractmethod
    def create_collection_names(self):
        """Create a collection names handler.

        Returns a handler that can list collections in the database,
        optionally filtered by name pattern.
        """
        ...

    @abstractmethod
    def create_collection_schema(self):
        """Create a collection schema handler.

        Returns a handler that can infer the schema of a collection
        by sampling documents and analyzing field types.
        """
        ...

    @abstractmethod
    def create_collection_indexes(self):
        """Create a collection indexes handler.

        Returns a handler that can list indexes on a collection.
        """
        ...

    @abstractmethod
    def create_query_executor(self):
        """Create a document query executor handler.

        Returns a handler that can execute queries (find, aggregate)
        against collections.
        """
        ...

    @abstractmethod
    def create_explain(self):
        """Create an execution plan handler.

        Returns a handler that can run ``explain`` on a query to
        produce the execution plan.
        """
        ...
