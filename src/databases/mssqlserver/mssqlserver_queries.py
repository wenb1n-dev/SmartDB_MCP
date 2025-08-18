from typing import List


class MSSQLServerQueries:
    @staticmethod
    def get_db_version() -> str:
        """
        获取数据库版本的SQL查询

        Returns:
            SQL查询语句
        """
        return "SELECT @@VERSION;"

    @staticmethod
    def get_table_names(database: str, schema: str, text: str) -> str:
        """
        根据注释获取表名的SQL查询

        Args:
            schema: 数据库名称
            text: 表注释关键词

        Returns:
            SQL查询语句
        """
        db_prefix = f"[{database}]."
        sql = f"""
            SELECT 
                    s.name AS TABLE_SCHEMA,
                    t.name AS TABLE_NAME,
                    CAST(ep.value AS NVARCHAR(500)) AS TABLE_COMMENT
                FROM 
                    {db_prefix}sys.tables t
                INNER JOIN 
                    {db_prefix}sys.schemas s ON t.schema_id = s.schema_id
                LEFT JOIN 
                    {db_prefix}sys.extended_properties ep ON t.object_id = ep.major_id 
                    AND ep.minor_id = 0 
                    AND ep.name = 'MS_Description'
                WHERE 
                    s.name = '{schema}'  
        """

        if "SEARCH_ALL_TABLES" != text:
            sql += (
                f"and ( AND CAST(ep.value AS NVARCHAR(500))  LIKE '%{text}%' "
                f"OR t.name LIKE '%{text}%' )"
            )

        return sql

    @staticmethod
    def get_table_description(database:str, schema: str, table_names: List[str]) -> str:

        db_prefix = f"[{database}]."

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
                SELECT 
                c.TABLE_NAME,
                c.COLUMN_NAME,
                c.DATA_TYPE,
                ISNULL(ep.value, '') AS COLUMN_COMMENT
            FROM {db_prefix}INFORMATION_SCHEMA.COLUMNS c
            LEFT JOIN {db_prefix}SYS.EXTENDED_PROPERTIES ep 
                ON ep.major_id = OBJECT_ID(c.TABLE_SCHEMA + '.' + c.TABLE_NAME)
                AND ep.minor_id = c.ORDINAL_POSITION
                AND ep.name = 'MS_Description'
            WHERE 
                c.TABLE_SCHEMA = '{schema}'
                AND c.TABLE_NAME IN ('{table_condition}')
            ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION;
                       """

    @staticmethod
    def get_table_index(database:str, schema: str, table_names: List[str]) -> str:
        db_prefix = f"[{database}]."

        table_condition = "','".join(table_names)

        return f"""
            SELECT 
                t.name AS TABLE_NAME,
                i.name AS INDEX_NAME,
                c.name AS COLUMN_NAME,
                ic.key_ordinal AS SEQ_IN_INDEX,
                CASE WHEN i.is_unique = 0 THEN 1 ELSE 0 END AS NON_UNIQUE,
                i.type_desc AS INDEX_TYPE
            FROM 
                {db_prefix}sys.indexes i
            INNER JOIN 
                {db_prefix}sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            INNER JOIN 
                {db_prefix}sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            INNER JOIN 
                {db_prefix}sys.tables t ON i.object_id = t.object_id
            INNER JOIN 
                {db_prefix}sys.schemas s ON t.schema_id = s.schema_id
            WHERE 
                s.name = '{schema}'  
                AND t.name IN ('{table_condition}') 
                AND i.type_desc != 'HEAP' 
            ORDER BY 
                t.name, i.name, ic.key_ordinal;
            """

    @staticmethod
    def get_max_connections() -> str:
        return """
            SELECT 
                name, 
                value, 
                value_in_use 
            FROM 
                sys.configurations 
            WHERE 
                name = 'user connections';

        """

    @staticmethod
    def get_current_connections () -> str:
       return """
            SELECT 
                s.session_id,
                s.login_name,
                s.host_name,
                s.program_name,
                s.client_interface_name,
                s.login_time,
                s.last_request_start_time,
                s.last_request_end_time,
                s.status,
                s.cpu_time,
                s.memory_usage,
                s.reads,
                s.writes,
                s.logical_reads
            FROM sys.dm_exec_sessions s
            WHERE s.is_user_process = 1
            ORDER BY s.last_request_start_time DESC;
        """

    @staticmethod
    def get_lock_requests():
        return """
        SELECT
            r.session_id AS waiting_session_id,
            r.blocking_session_id,
            r.wait_type,
            r.wait_time,
            r.wait_resource,
            t.text AS waiting_sql_text,
            r.status,
            r.command,
            r.cpu_time,
            r.logical_reads
        FROM sys.dm_exec_requests r
                 CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
        WHERE r.blocking_session_id <> 0;
        """

    @staticmethod
    def get_lock_detail():
        return """
        SELECT
            tl.request_session_id AS waiting_session_id,
            wt.blocking_session_id,
            DB_NAME(tl.resource_database_id) AS database_name,
            tl.resource_type,
            tl.resource_subtype,
            tl.resource_description,
            tl.request_mode AS requested_lock_mode,
            tl.request_status,
            s.login_name AS waiting_user,
            s.host_name AS waiting_host,
            s.program_name AS waiting_program,
            b.login_name AS blocking_user,
            b.host_name AS blocking_host,
            b.program_name AS blocking_program
        FROM sys.dm_tran_locks tl
                 INNER JOIN sys.dm_os_waiting_tasks wt ON tl.lock_owner_address = wt.resource_address
                 INNER JOIN sys.dm_exec_sessions s ON tl.request_session_id = s.session_id
                 INNER JOIN sys.dm_exec_sessions b ON wt.blocking_session_id = b.session_id
        WHERE tl.request_status = 'WAIT';
        """

    @staticmethod
    def get_lock_session():
        return """
        SELECT 
            r.session_id AS blocking_session_id,
            s.login_name,
            s.host_name,
            s.program_name,
            s.login_time,
            s.last_request_start_time,
            s.last_request_end_time,
            s.status,
            s.cpu_time,
            s.memory_usage,
            s.reads,
            s.writes,
            s.logical_reads,
            t.task_state,
            t.context_switches_count,
            t.pending_io_count,
            st.text AS blocking_sql_text
        FROM sys.dm_exec_requests r
        INNER JOIN sys.dm_exec_sessions s ON r.session_id = s.session_id
        INNER JOIN sys.dm_os_tasks t ON s.session_id = t.session_id
        OUTER APPLY sys.dm_exec_sql_text(r.sql_handle) st
        WHERE r.session_id IN (
            SELECT blocking_session_id 
            FROM sys.dm_exec_requests 
            WHERE blocking_session_id <> 0
        )
        AND s.is_user_process = 1;
        """

    @staticmethod
    def get_buffer_pool():
        return """
        SELECT 
            (CAST(SUM(CASE WHEN counter_name = 'Buffer cache hit ratio' THEN cntr_value ELSE 0 END) AS FLOAT) /
            CAST(SUM(CASE WHEN counter_name = 'Buffer cache hit ratio base' THEN cntr_value ELSE 0 END) AS FLOAT)) * 100 AS buffer_cache_hit_ratio
        FROM sys.dm_os_performance_counters
        WHERE object_name LIKE '%Buffer Manager%'
          AND counter_name IN ('Buffer cache hit ratio', 'Buffer cache hit ratio base');
        """

    @staticmethod
    def get_buffer_ple():
        return """
        SELECT 
            instance_name AS database_name,
            counter_name,
            cntr_value 
        FROM 
            sys.dm_os_performance_counters 
        WHERE 
            object_name LIKE '%Buffer Manager%'
            AND counter_name in ('Free pages','Page life expectancy'); 
        """

    @staticmethod
    def get_tmp_table():
        return """
        SELECT 
            SUM(user_object_reserved_page_count) * 8 / 1024 AS user_objects_mb,
            SUM(internal_object_reserved_page_count) * 8 / 1024 AS internal_objects_mb
        FROM 
            sys.dm_db_file_space_usage;
        """

    @staticmethod
    def get_io_info():
        return """
        SELECT 
            file_id,
            io_stall_read_ms,
            num_of_reads,
            io_stall_write_ms,
            num_of_writes
        FROM 
            sys.dm_io_virtual_file_stats(DB_ID(), NULL);
        """

    @staticmethod
    def get_memory_info():
        return """
        SELECT 
            counter_name,
            cntr_value,
            CASE 
                WHEN counter_name = 'Page life expectancy' THEN 'seconds'
                WHEN counter_name LIKE '%Memory%' THEN 'KB'
                WHEN counter_name LIKE '%Node Memory%' THEN 'KB'
                ELSE ''
            END AS unit
        FROM sys.dm_os_performance_counters
        WHERE object_name LIKE '%Memory Manager%'
          AND instance_name = ''
          AND counter_name IN ('Total Server Memory (KB)', 'Target Server Memory (KB)', 'Database Cache Memory (KB)', 'Free Memory (KB)', 'Stolen Memory (KB)')
        UNION ALL
        SELECT 
            'Page life expectancy' AS counter_name,
            cntr_value,
            'seconds' AS unit
        FROM sys.dm_os_performance_counters
        WHERE object_name LIKE '%Buffer Node%'
          AND counter_name = 'Page life expectancy'
          AND instance_name = '';
        """