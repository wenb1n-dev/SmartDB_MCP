"""Search engine data source abstraction.

Defines the :class:`SearchEngineFactory` ABC for search engine data sources.
Search engines have their own operation set: DSL query execution, index
mapping querying, and index listing.

Common operations (db_version, db_health) are inherited from
:class:`DataSourceFactory`.
"""

from abc import abstractmethod
from typing import ClassVar

from datasource.base import DataSourceFactory, Paradigm


class SearchEngineFactory(DataSourceFactory):
    """Abstract base class for search engine data source factories.

    Subclasses (e.g., ``ElasticsearchFactory``) implement the
    search-engine-specific abstract methods defined here. The ``paradigm``
    is set to ``Paradigm.SEARCH_ENGINE``.
    """

    paradigm: ClassVar[Paradigm] = Paradigm.SEARCH_ENGINE

    @abstractmethod
    def create_query_executor(self):
        """Create a DSL query executor handler.

        Returns a handler that can execute Elasticsearch DSL queries
        (search, aggregations, etc.).
        """
        ...

    @abstractmethod
    def create_index_mapping(self):
        """Create an index mapping handler.

        Returns a handler that can query index mappings (field types,
        analyzers, settings).
        """
        ...

    @abstractmethod
    def create_index_lister(self):
        """Create an index lister handler.

        Returns a handler that can list indices in the cluster,
        optionally filtered by pattern.
        """
        ...
