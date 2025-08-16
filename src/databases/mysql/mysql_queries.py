from typing import List


class MySQLQueries:
    """
    MySQL数据库查询语句集合
    将所有MySQL相关的SQL查询集中管理，提高代码的可维护性和重用性
    """

    @staticmethod
    def get_db_version() -> str:
        """
        获取数据库版本的SQL查询
        
        Returns:
            SQL查询语句
        """
        return "SELECT VERSION();"

    @staticmethod
    def get_table_names(database: str, text: str) -> str:
        """
        根据注释获取表名的SQL查询
        
        Args:
            database: 数据库名称
            text: 表注释关键词
            
        Returns:
            SQL查询语句
        """

        sql = f"""
        SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_COMMENT 
            FROM information_schema.TABLES WHERE 
            TABLE_SCHEMA = '{database}'
        """

        if "SEARCH_ALL_TABLES" != text:
           sql += f"AND ( TABLE_COMMENT LIKE '%{text}%' or TABLE_NAME LIKE '%{text}%'); "

        return sql

    @staticmethod
    def get_table_description(database: str, table_names: List[str]) -> str:
        """
        获取表结构描述的SQL查询
        
        Args:
            database: 数据库名称
            table_names: 表名列表
            
        Returns:
            SQL查询语句
        """
        table_condition = "','".join(table_names)
        return f"""
            SELECT TABLE_NAME, COLUMN_NAME, COLUMN_COMMENT 
            FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '{database}' 
            AND TABLE_NAME IN ('{table_condition}') ORDER BY TABLE_NAME, ORDINAL_POSITION;
            """

    @staticmethod
    def get_table_index(database: str, table_names: List[str]):
        table_condition = "','".join(table_names)
        return f"""
            SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME, SEQ_IN_INDEX, NON_UNIQUE, INDEX_TYPE 
            FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = '{database}' 
            AND TABLE_NAME IN ('{table_condition}') ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;
        """

    @staticmethod
    def get_db_health_index_redundant(database:str):
        return f"""
            SELECT object_name,index_name,count_star from performance_schema.table_io_waits_summary_by_index_usage 
            WHERE object_schema = '{database}' and count_star = 0 AND sum_timer_wait = 0 ;
        """
    @staticmethod
    def get_db_health_index_slow(database:str):
        """
        获取索引慢查询
        """
        return f"""
            SELECT object_schema,object_name,index_name,(max_timer_wait / 1000000000000) max_timer_wait 
            FROM performance_schema.table_io_waits_summary_by_index_usage where object_schema = '{database}' 
            and index_name is not null ORDER BY  max_timer_wait DESC;
        """
    @staticmethod
    def get_slow_unused_index_top5(database:str):
        return f"""
            SELECT object_schema,object_name, (max_timer_wait / 1000000000000) max_timer_wait 
            FROM performance_schema.table_io_waits_summary_by_index_usage where object_schema = '{database}' 
            and index_name IS null and max_timer_wait > 30000000000000 ORDER BY max_timer_wait DESC limit 5;

        """

    @staticmethod
    def get_current_connections():
        return """
        SHOW VARIABLES LIKE 'max_connections';
        SHOW STATUS LIKE 'Threads_connected';
        SHOW STATUS LIKE 'Threads_running';
        """

    @staticmethod
    def get_connection_errors():
        return """
        SHOW STATUS LIKE 'Connection_errors_%';
        SHOW STATUS LIKE 'Aborted_connects';
        """

    @staticmethod
    def get_active_processes():
        return """
        SHOW FULL PROCESSLIST;
        """

    @staticmethod
    def get_blocking():
        return """
        SHOW ENGINE INNODB STATUS;
        SELECT * FROM INFORMATION_SCHEMA.INNODB_TRX;
        SHOW OPEN TABLES WHERE In_use > 0;
        select * from information_schema.innodb_locks;
        select * from information_schema.innodb_lock_waits;
        select * from performance_schema.data_lock_waits;
        select * from performance_schema.data_locks;
        """

    @staticmethod
    def get_buffer_pool():
        return """
        SELECT 
            ROUND(
                (1 - (variable_value / (
                    SELECT variable_value 
                    FROM performance_schema.global_status 
                    WHERE variable_name = 'Innodb_buffer_pool_read_requests'))
                ) * 100, 
                2
            ) AS buffer_pool_hit_ratio
        FROM 
            performance_schema.global_status 
        WHERE 
            variable_name = 'Innodb_buffer_pool_reads';
        """

    @staticmethod
    def get_tmp_table():
        return """
        SELECT
            variable_name,
            variable_value
        FROM
            performance_schema.global_status
        WHERE
            variable_name IN ('Created_tmp_tables', 'Created_tmp_disk_tables');
        """

    @staticmethod
    def get_io_info():
        return """
        SELECT
            SUBSTR(event_name, 24) AS event,
            count_star AS total_count,
            sum_timer_wait AS total_latency,
            min_timer_wait AS min_latency,
            avg_timer_wait AS avg_latency,
            max_timer_wait AS max_latency
        FROM
            performance_schema.events_waits_summary_global_by_event_name
        WHERE
            event_name LIKE 'wait/io/file/innodb/%'
        ORDER BY
            sum_timer_wait DESC;
        """