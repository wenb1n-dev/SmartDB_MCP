"""MongoDB collection schema inference handler.

Infers the schema of a MongoDB collection by sampling documents and
analyzing field types, similar to the $jsonSchema aggregator.
"""

import json
from collections import defaultdict
from typing import Any, Dict, List

from bson import json_util

from connection.pool_manager import MultiDBPoolManager
from config.dbconfig import get_db_config_by_name


class MongoDBSchemaInference:
    """Infer schema of a MongoDB collection."""

    def get_collection_schema(
        self,
        pool_name: str,
        collection: str,
        sample_size: int = 1000,
    ) -> str:
        """Infer collection schema by sampling documents.

        Args:
            pool_name: Connection pool name.
            collection: Collection name.
            sample_size: Number of documents to sample (default: 1000).

        Returns:
            JSON-formatted schema description.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        config = get_db_config_by_name(pool_name)
        db_name = config.get("database", "admin")

        with pool.connection() as client:
            db = client[db_name]
            coll = db[collection]

            try:
                # Get collection stats
                try:
                    stats = db.command("collstats", collection)
                    doc_count = stats.get("count", 0)
                    size = stats.get("size", 0)
                    storage_size = stats.get("storageSize", 0)
                except Exception:
                    doc_count = size = storage_size = "N/A"

                # Sample documents
                sample_docs = list(coll.find().limit(sample_size))

                if not sample_docs:
                    return f"集合 '{collection}' 为空或不存在，无法推断 Schema"

                # Analyze field types
                field_types = defaultdict(set)
                field_count = defaultdict(int)
                total_sampled = len(sample_docs)

                for doc in sample_docs:
                    for key, value in self._flatten_doc(doc):
                        field_types[key].add(self._get_type_name(value))
                        field_count[key] += 1

                # Build schema
                schema = {
                    "collection": collection,
                    "sampled_documents": total_sampled,
                    "total_documents": doc_count,
                    "collection_size": size,
                    "storage_size": storage_size,
                    "fields": [],
                }

                for field_name in sorted(field_types.keys()):
                    types = sorted(field_types[field_name])
                    presence = field_count[field_name]
                    presence_pct = round(presence / total_sampled * 100, 1) if total_sampled > 0 else 0

                    schema["fields"].append({
                        "field": field_name,
                        "types": types,
                        "presence": f"{presence}/{total_sampled} ({presence_pct}%)",
                    })

                return json.dumps(schema, default=json_util.default, ensure_ascii=False, indent=2)

            except Exception as e:
                return f"推断 Schema 失败: {str(e)}"

    def _flatten_doc(self, doc: Dict[str, Any], prefix: str = "") -> List[tuple]:
        """Flatten a nested document into field paths.

        Args:
            doc: The document to flatten.
            prefix: Current field path prefix.

        Returns:
            List of (field_path, value) tuples.
        """
        result = []
        for key, value in doc.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict) and not key.startswith("$"):
                # Recurse into nested documents (but not operators like $date)
                result.extend(self._flatten_doc(value, full_key))
            elif isinstance(value, list):
                result.append((full_key, value))
                # Sample first element of list if it's a dict
                if value and isinstance(value[0], dict):
                    result.extend(self._flatten_doc(value[0], f"{full_key}[]"))
            else:
                result.append((full_key, value))

        return result

    def _get_type_name(self, value: Any) -> str:
        """Get the MongoDB/BSON type name for a value."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "double"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            # Handle BSON types
            type_name = type(value).__name__
            if type_name == "ObjectId":
                return "objectId"
            elif type_name == "datetime":
                return "date"
            elif type_name == "bytes":
                return "binData"
            return type_name
