"""Milvus factory implementation.

Registers with FactoryRegistry and provides handlers for all vector
operations: vector search, collection info, index info, version query,
and health check.
"""

from datasource.base import Paradigm
from datasource.vector.base import VectorFactory
from datasource.vector.milvus.milvus_collection_info import MilvusCollectionInfo
from datasource.vector.milvus.milvus_db_version import MilvusDatabaseVersion
from datasource.vector.milvus.milvus_health import MilvusHealth
from datasource.vector.milvus.milvus_index_info import MilvusIndexInfo
from datasource.vector.milvus.milvus_search import MilvusVectorSearch
from permission.milvus_permission import MilvusPermissionPolicy


class MilvusFactory(VectorFactory):
    """Factory for Milvus data source operations.

    This factory is registered with ``FactoryRegistry`` under the name
    ``"milvus"``. It creates handlers for vector search, collection
    info querying, index info querying, version query, and health check.
    """

    name: str = "milvus"
    paradigm = Paradigm.VECTOR

    def create_db_version(self) -> MilvusDatabaseVersion:
        return MilvusDatabaseVersion()

    def create_db_health(self) -> MilvusHealth:
        return MilvusHealth()

    def create_vector_search(self) -> MilvusVectorSearch:
        return MilvusVectorSearch()

    def create_collection_info(self) -> MilvusCollectionInfo:
        return MilvusCollectionInfo()

    def create_index_info(self) -> MilvusIndexInfo:
        return MilvusIndexInfo()

    def create_permission_policy(self) -> MilvusPermissionPolicy:
        return MilvusPermissionPolicy()
