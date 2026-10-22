"""Document paradigm data source package.

Defines the DocumentFactory ABC and imports concrete document implementations
(e.g., MongoDB) when their driver libraries are available.
"""

import importlib.util

from datasource.document.base import DocumentFactory

__all__ = ["DocumentFactory"]

if importlib.util.find_spec("pymongo"):
    from datasource.document.mongodb.mongodb_factory import MongoDBFactory  # noqa: F401
    __all__.append("MongoDBFactory")
