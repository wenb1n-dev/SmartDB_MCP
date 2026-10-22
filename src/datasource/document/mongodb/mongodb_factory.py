"""MongoDB factory implementation.

Registers with FactoryRegistry and provides handlers for all document
operations: collection listing, schema inference, index querying,
query execution, execution plan, version query, and health check.
"""

from datasource.base import Paradigm
from datasource.document.base import DocumentFactory
from datasource.document.mongodb.mongodb_collections import MongoDBCollections
from datasource.document.mongodb.mongodb_db_version import MongoDBDatabaseVersion
from datasource.document.mongodb.mongodb_explain import MongoDBExplain
from datasource.document.mongodb.mongodb_health import MongoDBHealth
from datasource.document.mongodb.mongodb_indexes import MongoDBIndexes
from datasource.document.mongodb.mongodb_queries import MongoDBQueryExecutor
from datasource.document.mongodb.mongodb_schema import MongoDBSchemaInference
from datasource.document.mongodb.mongodb_writer import MongoDBWriteExecutor
from permission.mongo_permission import MongoPermissionPolicy


class MongoDBFactory(DocumentFactory):
    """Factory for MongoDB data source operations.

    This factory is registered with ``FactoryRegistry`` under the name
    ``"mongodb"``. It creates handlers for collection listing, schema
    inference, index querying, query execution, execution plan,
    version query, and health check.
    """

    name: str = "mongodb"
    paradigm = Paradigm.DOCUMENT

    def create_db_version(self) -> MongoDBDatabaseVersion:
        return MongoDBDatabaseVersion()

    def create_db_health(self) -> MongoDBHealth:
        return MongoDBHealth()

    def create_collection_names(self) -> MongoDBCollections:
        return MongoDBCollections()

    def create_collection_schema(self) -> MongoDBSchemaInference:
        return MongoDBSchemaInference()

    def create_collection_indexes(self) -> MongoDBIndexes:
        return MongoDBIndexes()

    def create_query_executor(self) -> MongoDBQueryExecutor:
        return MongoDBQueryExecutor()

    def create_explain(self) -> MongoDBExplain:
        return MongoDBExplain()

    def create_write_executor(self) -> MongoDBWriteExecutor:
        return MongoDBWriteExecutor()

    def create_permission_policy(self) -> MongoPermissionPolicy:
        return MongoPermissionPolicy()
