"""Vector store data source abstraction.

Defines the :class:`VectorFactory` ABC for vector database data sources.
Vector stores have their own operation set: similarity search, collection
info querying, and index info querying.

Common operations (db_version, db_health) are inherited from
:class:`DataSourceFactory`.
"""

from abc import abstractmethod
from typing import ClassVar

from datasource.base import DataSourceFactory, Paradigm


class VectorFactory(DataSourceFactory):
    """Abstract base class for vector data source factories.

    Subclasses (e.g., ``MilvusFactory``) implement the vector-specific
    abstract methods defined here. The ``paradigm`` is set to
    ``Paradigm.VECTOR``.
    """

    paradigm: ClassVar[Paradigm] = Paradigm.VECTOR

    @abstractmethod
    def create_vector_search(self):
        """Create a vector search handler.

        Returns a handler that can perform similarity search on vector
        collections, supporting different distance metrics and filters.
        """
        ...

    @abstractmethod
    def create_collection_info(self):
        """Create a collection info handler.

        Returns a handler that can query collection metadata: name,
        dimension, distance metric, schema, etc.
        """
        ...

    @abstractmethod
    def create_index_info(self):
        """Create an index info handler.

        Returns a handler that can query index information: index type
        (HNSW/IVF/DISKANN), parameters, build progress, etc.
        """
        ...
