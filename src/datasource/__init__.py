"""Data source abstraction package.

This package provides the top-level abstraction for all data source types.
The DataSourceFactory and Paradigm are the main abstractions defined here.
FactoryRegistry is defined in datasource.registry and serves as the global
registry for all paradigms (relational and non-relational).

Unified registration flow:
1. Import all paradigm sub-packages (relational, kv, document, vector,
   search_engine, message_queue). Each sub-package imports its concrete
   factory modules, triggering ``DataSourceFactory.__init_subclass__``
   which adds each factory to ``FactoryRegistry._pending``.
2. Call ``FactoryRegistry.register_pending()`` to batch-register all
   pending factories.

Optional driver dependencies are handled by each paradigm sub-package's
``__init__.py`` using ``importlib.util.find_spec()`` to check if the driver
library is installed before importing the concrete factory.
"""

from datasource.base import DataSourceFactory, Paradigm, DatabaseVersion, DatabaseHealth
from datasource.registry import FactoryRegistry

__all__ = [
    "DataSourceFactory",
    "Paradigm",
    "DatabaseVersion",
    "DatabaseHealth",
    "FactoryRegistry",
]

# Step 1: Import all paradigm packages. This triggers __init_subclass__
# for each concrete factory, adding them to FactoryRegistry._pending.
import datasource.relational  # noqa: F401, E402
import datasource.kv  # noqa: F401, E402
import datasource.document  # noqa: F401, E402
import datasource.vector  # noqa: F401, E402
import datasource.search_engine  # noqa: F401, E402
import datasource.message_queue  # noqa: F401, E402

# Step 2: Register all pending factories.
FactoryRegistry.register_pending()
