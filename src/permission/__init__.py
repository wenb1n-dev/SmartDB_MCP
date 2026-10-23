"""Permission policy abstraction package.

Exports the permission policy ABC and the SQL permission policy implementation
for use by other modules (e.g., SQL execution utilities).
"""

"""Permission policy package.

注意：为避免 permission -> datasource -> utils -> permission 的包初始化循环，
需要运行期鉴权入口时请直接导入 ``permission.enforcer``。
"""

from permission.base import (
    CategoryBasedPermissionPolicy,
    PermissionPolicy,
    SqlPermissionPolicy,
)
from permission.operations import OperationCategory, SQLOperation
from permission.roles import Role

__all__ = [
    "CategoryBasedPermissionPolicy",
    "OperationCategory",
    "PermissionPolicy",
    "Role",
    "SQLOperation",
    "SqlPermissionPolicy",
]
