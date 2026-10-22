"""Elasticsearch factory implementation.

Registers with FactoryRegistry and provides handlers for all search engine
operations: DSL query, index mapping, index listing, version query, and health check.
"""

from datasource.base import Paradigm
from datasource.search_engine.base import SearchEngineFactory
from datasource.search_engine.elasticsearch.es_db_version import ElasticsearchDatabaseVersion
from datasource.search_engine.elasticsearch.es_health import ElasticsearchHealth
from datasource.search_engine.elasticsearch.es_indices import ElasticsearchIndices
from datasource.search_engine.elasticsearch.es_mapping import ElasticsearchMapping
from datasource.search_engine.elasticsearch.es_query import ElasticsearchQueryExecutor
from permission.es_permission import ESPermissionPolicy


class ElasticsearchFactory(SearchEngineFactory):
    """Factory for Elasticsearch data source operations.

    This factory is registered with ``FactoryRegistry`` under the name
    ``"elasticsearch"``. It creates handlers for DSL query execution,
    index mapping querying, index listing, version query, and health check.
    """

    name: str = "elasticsearch"
    paradigm = Paradigm.SEARCH_ENGINE

    def create_db_version(self) -> ElasticsearchDatabaseVersion:
        return ElasticsearchDatabaseVersion()

    def create_db_health(self) -> ElasticsearchHealth:
        return ElasticsearchHealth()

    def create_query_executor(self) -> ElasticsearchQueryExecutor:
        return ElasticsearchQueryExecutor()

    def create_index_mapping(self) -> ElasticsearchMapping:
        return ElasticsearchMapping()

    def create_index_lister(self) -> ElasticsearchIndices:
        return ElasticsearchIndices()

    def create_permission_policy(self) -> ESPermissionPolicy:
        return ESPermissionPolicy()
