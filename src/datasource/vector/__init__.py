"""Vector paradigm data source package.

Defines the VectorFactory ABC and imports concrete vector implementations
(e.g., Milvus) when their driver libraries are available.
"""

import importlib.util

from datasource.vector.base import VectorFactory

__all__ = ["VectorFactory"]

if importlib.util.find_spec("pymilvus"):
    from datasource.vector.milvus.milvus_factory import MilvusFactory  # noqa: F401
    __all__.append("MilvusFactory")
