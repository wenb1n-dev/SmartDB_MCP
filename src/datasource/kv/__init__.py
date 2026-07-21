"""KV data source paradigm package.

Defines the KVStoreFactory ABC and is imported by concrete KV
implementations (e.g., Redis).
"""

from datasource.kv.base import KVStoreFactory

__all__ = ["KVStoreFactory"]
