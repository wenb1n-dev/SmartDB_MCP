"""Database package init.

This file now handles the registration of all database factory classes
after they have been imported to prevent circular import issues.
"""

# 首先导入基础工厂类
from .database_factory import DatabaseOperationFactory, register_all_factories

# 然后导入所有具体工厂实现
from .mysql.mysql_factory import MySQLFactory
from .postgresql.postgresql_factory import PostgresqlFactory
from .oracle.oracle_factory import OracleFactory
from .mssqlserver.sqlserver_factory import MSSQLServerFactory
from .dameng.dameng_factory import DamengFactory

# 最后注册所有工厂类
register_all_factories()

__all__ = ['DatabaseOperationFactory', 'MySQLFactory', 'PostgresqlFactory', 'OracleFactory', 'MSSQLServerFactory', 'DamengFactory']