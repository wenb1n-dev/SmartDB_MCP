from config.dbconfig import get_db_config_by_name
from databases.base.base import DatabaseHealth
from typing import Dict, Any

from databases.oracle.oracle_queries import OracleQueries
from utils.execute_sql_util import ExecuteSqlUtil


class OracleHealth(DatabaseHealth):
    """
    Oracle数据库健康检查类
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
        # 当前连接数
        current_connections_sql = OracleQueries.get_current_connections()
        current_connections_result = ExecuteSqlUtil.execute_single_statement(pool_name, current_connections_sql)

        # 最大连接数
        max_connections_sql = OracleQueries.get_max_connections()
        max_connections_result = ExecuteSqlUtil.execute_single_statement(pool_name, max_connections_sql)

        # 构建结果字符串
        result_parts = []
        result_parts.append("- 当前用户连接数:")
        result_parts.append(ExecuteSqlUtil.format_result(current_connections_result))
        result_parts.append("- processes资源的当前使用情况和限制:")
        result_parts.append(ExecuteSqlUtil.format_result(max_connections_result))

        return "\n".join(result_parts)

    def get_db_blocking(self, pool_name: str, db_config: Dict[str, Any]) -> str:
        blocking_sql = OracleQueries.get_blocking()
        blocking_result = ExecuteSqlUtil.execute_single_statement(pool_name, blocking_sql)

        locking_sql = OracleQueries.get_locking()
        locking_result = ExecuteSqlUtil.execute_single_statement(pool_name, locking_sql)

        trx_sql = OracleQueries.get_trx()
        trx_result = ExecuteSqlUtil.execute_single_statement(pool_name, trx_sql)

        # 构建结果字符串
        result_parts = []
        result_parts.append("- 递归阻塞链信息")
        result_parts.append(ExecuteSqlUtil.format_result(blocking_result))
        result_parts.append("- 被锁对象详情:")
        result_parts.append(ExecuteSqlUtil.format_result(locking_result))
        result_parts.append("- 超过5分钟的事务:")
        result_parts.append(ExecuteSqlUtil.format_result(trx_result))

        return "\n".join(result_parts)

    def get_db_resources(self, pool_name: str, db_config: Dict[str, Any]) -> str:

        buffer_pool_sql = OracleQueries.get_buffer_pool()
        buffer_pool_result = ExecuteSqlUtil.execute_single_statement(pool_name, buffer_pool_sql)

        tmp_sql = OracleQueries.get_tmp_table()
        tmp_result = ExecuteSqlUtil.execute_single_statement(pool_name, tmp_sql)

        io_sql = OracleQueries.get_io_info()
        io_result = ExecuteSqlUtil.execute_single_statement(pool_name, io_sql)

        sga_status_sql = OracleQueries.get_sga_status()
        sga_status_result = ExecuteSqlUtil.execute_single_statement(pool_name, sga_status_sql)

        pga_status_sql = OracleQueries.get_pga_status()
        pga_status_result = ExecuteSqlUtil.execute_single_statement(pool_name, pga_status_sql)

        sga_total_sql = OracleQueries.get_sga_total()
        sga_total_result = ExecuteSqlUtil.execute_single_statement(pool_name, sga_total_sql)


        # 构建结果字符串
        result_parts = []
        result_parts.append("- 缓冲区缓存命中率:")
        result_parts.append(ExecuteSqlUtil.format_result(buffer_pool_result))
        result_parts.append("- 临时表空间使用情况:")
        result_parts.append(ExecuteSqlUtil.format_result(tmp_result))
        result_parts.append("- IO信息:")
        result_parts.append(ExecuteSqlUtil.format_result(io_result))
        result_parts.append("- SGA内存使用情况:")
        result_parts.append(ExecuteSqlUtil.format_result(sga_status_result))
        result_parts.append("- PGA内存使用情况:")
        result_parts.append(ExecuteSqlUtil.format_result(pga_status_result))
        result_parts.append("- SGA内存大小:")
        result_parts.append(ExecuteSqlUtil.format_result(sga_total_result))

        return "\n".join(result_parts)