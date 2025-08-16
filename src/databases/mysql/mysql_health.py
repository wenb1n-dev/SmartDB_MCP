from config.dbconfig import get_db_config_by_name
from databases.base.base import DatabaseHealth
from typing import Dict, Any, List

from databases.mysql.mysql_queries import MySQLQueries
from utils.execute_sql_util import ExecuteSqlUtil


class MySQLHealth(DatabaseHealth):

    def get_db_health(self, pool_name: str, health_type: str) -> str:
        db_config = get_db_config_by_name(pool_name)
        """
        根据健康检查类型执行相应的检查方法

        Args:
            pool_name: 数据库连接池名称
            health_type: 健康检查类型

        Returns:
            健康检查结果
        """
        # 定义类型到方法的映射
        health_methods = {
            #"index": self.get_db_index,
            "connection": self.get_db_connection,
            "blocking": self.get_db_blocking,
            "resources": self.get_db_resources
        }

        result: str = ""
        if health_type == "all":
            for check_type in health_methods:
                result += "\n".join(health_methods[check_type](pool_name,db_config))
        elif health_type in health_methods:
            method = health_methods[health_type]
            result = method(pool_name,db_config)
        else:
            raise ValueError(f"无效的健康检查类型: {health_type}")

        return  result

    def get_db_index(self, pool_name: str, db_config: Dict[str, Any]) -> str:
        """
        索引健康分析

        Args:
            pool_name: 数据库连接池名称

        Returns:
            索引健康分析结果
        """
        # 获取冗余索引情况
        redundant_sql = MySQLQueries.get_db_health_index_redundant(db_config["database"])
        redundant_result = ExecuteSqlUtil.execute_single_statement(pool_name, redundant_sql)

        # 获取性能较差的索引情况
        slow_sql = MySQLQueries.get_db_health_index_slow(db_config["database"])
        slow_result = ExecuteSqlUtil.execute_single_statement(pool_name, slow_sql)

        # 获取未使用索引查询时间大于30秒的top5情况
        unused_sql = MySQLQueries.get_slow_unused_index_top5(db_config["database"])
        unused_result = ExecuteSqlUtil.execute_single_statement(pool_name, unused_sql)

        # 格式化结果
        formatted_results = []
        formatted_results.append("- 冗余索引情况")
        formatted_results.append(ExecuteSqlUtil.format_result(redundant_result))
        formatted_results.append("\n- 性能较差的索引情况")
        formatted_results.append(ExecuteSqlUtil.format_result(slow_result))
        formatted_results.append("\n- 未使用索引查询时间大于30秒的top5情况")
        formatted_results.append(ExecuteSqlUtil.format_result(unused_result))
        
        return "\n".join(formatted_results)

    def get_db_connection(self, pool_name: str, db_config: Dict[str, Any]) -> str:
        """
        连接情况分析

        Args:
            pool_name: 数据库连接池名称

        Returns:
            连接情况分析结果
        """
        current_connections_sql = MySQLQueries.get_current_connections()
        current_connections_results = ExecuteSqlUtil.execute_multiple_statements(pool_name, current_connections_sql)
        
        connection_errors_sql = MySQLQueries.get_connection_errors()
        connection_errors_results = ExecuteSqlUtil.execute_multiple_statements(pool_name, connection_errors_sql)
        
        active_processes_sql = MySQLQueries.get_active_processes()
        active_processes_results = ExecuteSqlUtil.execute_multiple_statements(pool_name, active_processes_sql)
        
        # 格式化所有结果
        formatted_current_connections = []
        for result in current_connections_results:
            formatted_current_connections.append(ExecuteSqlUtil.format_result(result))
        
        formatted_connection_errors = []
        for result in connection_errors_results:
            formatted_connection_errors.append(ExecuteSqlUtil.format_result(result))
            
        formatted_active_processes = []
        for result in active_processes_results:
            formatted_active_processes.append(ExecuteSqlUtil.format_result(result))
        
        # 构建结果字符串
        result_parts = []
        result_parts.append("- 当前连接数和最大连接数")
        result_parts.append("\n".join(formatted_current_connections))
        result_parts.append("\n- 连接错误统计")
        result_parts.append("\n".join(formatted_connection_errors))
        result_parts.append("\n- 活跃进程列表")
        result_parts.append("\n".join(formatted_active_processes))
        
        return "\n".join(result_parts)

    def get_db_blocking(self, pool_name: str,db_config: Dict[str, Any]) -> str:
        blocking_sql = MySQLQueries.get_blocking()
        blocking_results = ExecuteSqlUtil.execute_multiple_statements(pool_name, blocking_sql)
        
        # 格式化所有结果
        formatted_blocking = []
        for result in blocking_results:
            formatted_blocking.append(ExecuteSqlUtil.format_result(result))
        
        # 构建结果字符串
        result_parts = []
        result_parts.append("- InnoDB 状态、事务、锁信息")
        result_parts.append("\n".join(formatted_blocking))
        
        return "\n".join(result_parts)

    def get_db_resources(self, pool_name: str,db_config:Dict[str,Any]):
        buffer_pool_sql = MySQLQueries.get_buffer_pool()
        buffer_pool_result = ExecuteSqlUtil.execute_single_statement(pool_name, buffer_pool_sql)
        formatted_buffer_pool = [ExecuteSqlUtil.format_result(buffer_pool_result)]

        tem_table_sql = MySQLQueries.get_tmp_table()
        tem_table_result = ExecuteSqlUtil.execute_single_statement(pool_name, tem_table_sql)
        formatted_tem_table = [ExecuteSqlUtil.format_result(tem_table_result)]

        io_sql = MySQLQueries.get_io_info()
        io_result = ExecuteSqlUtil.execute_single_statement(pool_name, io_sql)
        formatted_io = [ExecuteSqlUtil.format_result(io_result)]

        # 构建结果字符串
        result_parts = []
        result_parts.append("- 缓冲池命中率")
        result_parts.append("\n".join((formatted_buffer_pool)))
        result_parts.append("- 临时表使用信息")
        result_parts.append("\n".join((formatted_tem_table)))
        result_parts.append("- IO信息")
        result_parts.append("\n".join((formatted_io)))

        return "\n".join(result_parts)
