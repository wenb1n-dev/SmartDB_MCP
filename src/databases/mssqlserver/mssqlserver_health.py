from config.dbconfig import get_db_config_by_name
from databases.base.base import DatabaseHealth
from typing import Dict, Any

from databases.mssqlserver.mssqlserver_queries import MSSQLServerQueries
from utils.execute_sql_util import ExecuteSqlUtil


class MSSQLServerHealth(DatabaseHealth):
    """
    SQL Server数据库健康检查类
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
        """
        连接情况分析

        Args:
            pool_name: 数据库连接池名称
            db_config: 数据库配置

        Returns:
            连接情况分析结果
        """
        # 当前连接详情
        current_connections_sql = MSSQLServerQueries.get_current_connections()
        current_connections_result = ExecuteSqlUtil.execute_single_statement(pool_name, current_connections_sql)

        # 连接最大值配置
        max_connections_sql = MSSQLServerQueries.get_max_connections()
        max_connections_result = ExecuteSqlUtil.execute_single_statement(pool_name, max_connections_sql)

        # 构建结果字符串
        result_parts = []
        result_parts.append("- 连接详情:")
        result_parts.append(ExecuteSqlUtil.format_result(current_connections_result))
        result_parts.append("- 连接限制信息:")
        result_parts.append(ExecuteSqlUtil.format_result(max_connections_result))

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
        #
        lock_request_sql = MSSQLServerQueries.get_lock_request()
        lock_request_result = ExecuteSqlUtil.execute_single_statement(pool_name, lock_request_sql)

        lock_detail_sql = MSSQLServerQueries.get_lock_detail()
        lock_detail_result = ExecuteSqlUtil.execute_single_statement(pool_name, lock_detail_sql)

        lock_session_sql = MSSQLServerQueries.get_lock_session()
        lock_session_result = ExecuteSqlUtil.execute_single_statement(pool_name)

        # 构建结果字符串
        result_parts = []
        result_parts.append("- 当前被阻塞的请求:")
        result_parts.append(ExecuteSqlUtil.format_result(lock_request_result))
        result_parts.append("- 锁等待详情:")
        result_parts.append(ExecuteSqlUtil.format_result(lock_detail_result))
        result_parts.append("- 阻塞源头会话:")
        result_parts.append(ExecuteSqlUtil.format_result(lock_session_result))

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
        buffer_pool_sql = MSSQLServerQueries.get_buffer_pool()
        buffer_pool_result = ExecuteSqlUtil.execute_single_statement(pool_name, buffer_pool_sql)

        buffer_ple_sql = MSSQLServerQueries.get_buffer_ple()
        buffer_ple_result = ExecuteSqlUtil.execute_single_statement(pool_name, buffer_ple_sql)

        tmp_table_sql = MSSQLServerQueries.get_tmp_table()
        tmp_table_result = ExecuteSqlUtil.execute_single_statement(pool_name, tmp_table_sql)

        io_info_sql = MSSQLServerQueries.get_io_info()
        io_info_result = ExecuteSqlUtil.execute_single_statement(pool_name, io_info_sql)

        memory_sql = MSSQLServerQueries.get_memory_info()
        memory_result = ExecuteSqlUtil.execute_single_statement(pool_name, memory_sql)

        # 构建结果字符串
        result_parts = []
        result_parts.append("- 缓冲区缓存命中率:")
        result_parts.append(ExecuteSqlUtil.format_result(buffer_pool_result))
        result_parts.append("- 页生命周期（PLE）:")
        result_parts.append(ExecuteSqlUtil.format_result(buffer_ple_result))
        result_parts.append("- 临时表情况：")
        result_parts.append(ExecuteSqlUtil.format_result(tmp_table_result))
        result_parts.append("- 内存使用情况:")
        result_parts.append(ExecuteSqlUtil.format_result(memory_result))
        result_parts.append("- IO情况:")
        result_parts.append(ExecuteSqlUtil.format_result(io_info_result))

        return "\n".join(result_parts)