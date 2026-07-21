"""Permission policy abstraction package.

Exports the permission policy ABC and the SQL permission policy implementation
for use by other modules (e.g., SQL execution utilities).
"""

from permission.base import (
    PermissionPolicy,
    SqlPermissionPolicy,
    SQLOperation,
)

__all__ = [
    "PermissionPolicy",
    "SqlPermissionPolicy",
    "SQLOperation",
]
