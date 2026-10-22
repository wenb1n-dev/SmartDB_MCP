"""Search engine paradigm data source package.

Defines the SearchEngineFactory ABC and imports concrete search engine
implementations (e.g., Elasticsearch) when their driver libraries are available.
"""

import importlib.util

from datasource.search_engine.base import SearchEngineFactory

__all__ = ["SearchEngineFactory"]

if importlib.util.find_spec("elasticsearch"):
    from datasource.search_engine.elasticsearch.es_factory import ElasticsearchFactory  # noqa: F401
    __all__.append("ElasticsearchFactory")
