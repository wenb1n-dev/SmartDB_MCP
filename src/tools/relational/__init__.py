"""关系型范式工具（RELATIONAL）。

适用于 MySQL / PostgreSQL / Oracle / SQL Server / 达梦：
- execute_sql：执行 sql_creator 生成的 SQL（支持多语句）
- sql_creator：基于真实元数据生成 SQL 的唯一推荐入口
- sql_optimize：SQL 性能优化建议
- get_table_name / get_table_desc / get_table_index：表名、表结构、索引元数据
"""
