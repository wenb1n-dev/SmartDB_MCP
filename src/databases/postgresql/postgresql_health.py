from config.dbconfig import get_db_config_by_name
from databases.base.base import DatabaseHealth
from typing import Dict, Any

from databases.postgresql.postgresql_queries import PostgresqlQueries
from utils.execute_sql_util import ExecuteSqlUtil


class PostgresqlHealth(DatabaseHealth):
    """
    PostgreSQL数据库健康检查类
    """

    def get_db_health(self, pool_name: str, health_type: str) -> str:
        """
        根据健康检查类型执行相应的检查方法

        Args:
            pool_name: 数据库连接池名称
            health_type: 健康检查类型

        Returns:
            健康检查结果
        """
        db_config = get_db_config_by_name(pool_name)
        
        # 定义类型到方法的映射
        health_methods = {
            "connection": self.get_db_connection,
            "blocking": self.get_db_blocking,
            "resources": self.get_db_resources
        }

        result: str = ""
        if health_type == "all":
            for check_type in health_methods:
                result += health_methods[check_type](pool_name, db_config) + "\n\n"
        elif health_type in health_methods:
            method = health_methods[health_type]
            result = method(pool_name, db_config)
        else:
            raise ValueError(f"无效的健康检查类型: {health_type}")

        return result

    def get_db_connection(self, pool_name: str, db_config: Dict[str, Any]) -> str:

        max_connection_sql = PostgresqlQueries.get_max_connections()
        max_connection_result = ExecuteSqlUtil.execute_single_statement(pool_name, max_connection_sql)

        current_connection_sql = PostgresqlQueries.get_current_connections(db_config["database"])
        current_connection_result = ExecuteSqlUtil.execute_single_statement(pool_name, current_connection_sql)

        # 构建结果字符串
        result_parts = []
        result_parts.append("- 最大连接数配置:")
        result_parts.append(ExecuteSqlUtil.format_result(max_connection_result))
        result_parts.append("- 连接状态详情:")
        result_parts.append(ExecuteSqlUtil.format_result(current_connection_result))

        return "\n".join(result_parts)

    def get_db_blocking(self, pool_name: str, db_config: Dict[str, Any]) -> str:
        """
        锁等待和阻塞情况分析

        Args:
            pool_name: 数据库连接池名称
            db_config: 数据库配置

        Returns:
            锁等待和阻塞情况分析结果
        """
        # 锁等待信息
        lock_wait_sql = PostgresqlQueries.get_locking()

        lock_wait_result = ExecuteSqlUtil.execute_single_statement(pool_name, lock_wait_sql)

        # 构建结果字符串
        result_parts = []
        result_parts.append("- 当前锁等待信息:")
        result_parts.append(ExecuteSqlUtil.format_result(lock_wait_result))

        return "\n".join(result_parts)

    def get_db_resources(self, pool_name: str, db_config: Dict[str, Any]) -> str:
        """
        资源使用情况分析

        Args:
            pool_name: 数据库连接池名称
            db_config: 数据库配置

        Returns:
            资源使用情况分析结果
        """
        # 数据库大小
        database_size_sql = PostgresqlQueries.get_database_size()
        database_size_result = ExecuteSqlUtil.execute_single_statement(pool_name, database_size_sql)

        # 缓存命中率
        cache_hit_ratio_sql = PostgresqlQueries.get_buffer_pool()
        cache_hit_ratio_result = ExecuteSqlUtil.execute_single_statement(pool_name, cache_hit_ratio_sql)

        # 表大小TOP 10
        top_tables_sql = PostgresqlQueries.get_table_top10()
        top_tables_result = ExecuteSqlUtil.execute_single_statement(pool_name, top_tables_sql)

        # 后台写入统计
        bgwriter_stats_sql = PostgresqlQueries.get_bgwriter_stats()
        bgwriter_stats_result = ExecuteSqlUtil.execute_single_statement(pool_name, bgwriter_stats_sql)

        # 死元组
        dead_tup_sql = PostgresqlQueries.get_dead_tup()
        dead_tup_result = ExecuteSqlUtil.execute_single_statement(pool_name, dead_tup_sql)

        # 临时表
        tmp_table_sql = PostgresqlQueries.get_tmp_table()
        tmp_table_result = ExecuteSqlUtil.execute_single_statement(pool_name, tmp_table_sql)

        #io
        io_sql = PostgresqlQueries.get_io_info()
        io_result = ExecuteSqlUtil.execute_single_statement(pool_name, io_sql)

        # 事务 ID 年龄
        mxid_age_sql = PostgresqlQueries.get_mxid_age()
        mxid_age_result = ExecuteSqlUtil.execute_single_statement(pool_name, mxid_age_sql)


        # 构建结果字符串
        result_parts = []
        result_parts.append("- 数据库大小:")
        result_parts.append(ExecuteSqlUtil.format_result(database_size_result))
        result_parts.append("- 缓存命中率:")
        result_parts.append(ExecuteSqlUtil.format_result(cache_hit_ratio_result))
        result_parts.append("- 表大小TOP 10:")
        result_parts.append(ExecuteSqlUtil.format_result(top_tables_result))
        result_parts.append("- 后台写入统计:")
        result_parts.append(ExecuteSqlUtil.format_result(bgwriter_stats_result))
        result_parts.append("- 死元组情况：")
        result_parts.append(ExecuteSqlUtil.format_result(dead_tup_result))
        result_parts.append("- 临时表空间使用情况：")
        result_parts.append(ExecuteSqlUtil.format_result(tmp_table_result))
        result_parts.append("- IO信息：")
        result_parts.append(ExecuteSqlUtil.format_result(io_result))
        result_parts.append("- 事务 ID 年龄：")
        result_parts.append(ExecuteSqlUtil.format_result(mxid_age_result))

        return "\n".join(result_parts)