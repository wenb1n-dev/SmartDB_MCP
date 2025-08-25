from typing import List


class OracleQueries:
    @staticmethod
    def get_db_version() -> str:
        """
        获取数据库版本的SQL查询

        Returns:
            SQL查询语句
        """
        return "SELECT * FROM v$version"

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
            SELECT
                owner AS table_schema,
                table_name,
                comments AS table_comment
            FROM
                all_tab_comments
            WHERE
                owner = '{database}'
        """

        if "SEARCH_ALL_TABLES" != text:
            sql += (f"AND ((comments IS NOT NULL AND UPPER(comments) LIKE UPPER('%{text}%'))"
                    f"OR ( UPPER(table_name) LIKE UPPER('%{text}%')))")

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
               SELECT
                    col.table_name,
                    col.column_name,
                    col.DATA_TYPE,
                    com.comments AS column_comment
                FROM
                    all_tab_cols col
                        LEFT JOIN
                    all_col_comments com
                    ON col.owner = com.owner
                        AND col.table_name = com.table_name
                        AND col.column_name = com.column_name
                WHERE
                    col.owner = '{database}'
                  AND col.table_name IN ('{table_condition}')  
                ORDER BY
                    col.table_name, col.column_id
               """
    @staticmethod
    def get_table_index(database: str, table_names: List[str]):
        table_condition = "','".join(table_names)
        return f"""
            SELECT
                i.table_name AS TABLE_NAME,
                i.index_name AS INDEX_NAME,
                c.column_name AS COLUMN_NAME,
                c.column_position AS SEQ_IN_INDEX,
                CASE WHEN i.uniqueness = 'NONUNIQUE' THEN 1 ELSE 0 END AS NON_UNIQUE,
                i.index_type AS INDEX_TYPE
            FROM
                all_indexes i
                    JOIN
                all_ind_columns c
                ON i.index_name = c.index_name
                    AND i.table_owner = c.table_owner
                    AND i.table_name = c.table_name
            WHERE
                i.table_owner = '{database}'  
              AND i.table_name IN ('{table_condition}') 
            ORDER BY
                i.table_name, i.index_name, c.column_position
        """

    @staticmethod
    def get_max_connections():
        return """
        SELECT 
            resource_name, 
            current_utilization, 
            max_utilization, 
            limit_value 
        FROM 
            v$resource_limit 
        WHERE 
            resource_name = 'processes'
        """

    @staticmethod
    def get_current_connections ():
        return """
        SELECT
            s.sid,
            s.serial#,
            s.username,
            s.status,
            s.osuser,
            s.machine,
            s.program,
            s.module,
            s.action,
            s.client_info,
            s.logon_time,
            ROUND(s.last_call_et / 60, 2) AS last_call_min,
            s.state AS wait_state,
            s.event,
            s.wait_class,
            s.seconds_in_wait,
            s.sql_id,
            s.prev_sql_id,
            s.row_wait_obj# AS row_wait_object_id,
            s.row_wait_file# AS row_wait_file,
            s.row_wait_block# AS row_wait_block,
            s.blocking_session_status,
            s.blocking_instance,
            s.blocking_session,
            s.paddr
        FROM
            v$session s
        WHERE
            type != 'BACKGROUND'
        """

    @staticmethod
    def get_blocking():
        return """
        WITH blocking_tree AS (
            SELECT 
                'alter system kill session ''' || s.sid || ',' || s.serial# || ',@' || s.inst_id || ''' immediate;' AS kill_command,
                SYS_CONNECT_BY_PATH(s.sid || '@' || s.inst_id, ' ← ') AS blocking_path,
                s.inst_id,
                s.sid,
                s.serial#,
                s.username,
                s.osuser,
                s.machine,
                s.program,
                s.status,
                s.sql_id,
                s.event,
                s.blocking_session,
                s.blocking_instance,
                CONNECT_BY_ISLEAF AS is_blocked_end,
                LEVEL AS blocking_level,
                CASE WHEN lo.xidusn IS NOT NULL THEN 'YES' ELSE 'NO' END AS holds_locked_object
            FROM 
                gv$session s
                LEFT JOIN gv$locked_object lo ON s.sid = lo.session_id AND s.inst_id = lo.inst_id
            WHERE 
                s.blocking_session IS NOT NULL  
            CONNECT BY 
                (s.sid || '@' || s.inst_id) = PRIOR (s.blocking_session || '@' || s.blocking_instance)
            START WITH 
                s.blocking_session IS NOT NULL
        ),
       
        sql_texts AS (
            SELECT DISTINCT sql_id, sql_text 
            FROM gv$sql 
            WHERE sql_id IN (SELECT sql_id FROM blocking_tree WHERE sql_id IS NOT NULL)
        )
        
        SELECT 
            bt.kill_command,
            bt.blocking_path,
            bt.inst_id,
            bt.sid,
            bt.serial#,
            bt.username,
            bt.osuser,
            bt.machine,
            bt.program,
            bt.status,
            bt.event,
            bt.blocking_level,
            bt.holds_locked_object,
            st.sql_text
        FROM 
            blocking_tree bt
            LEFT JOIN sql_texts st ON bt.sql_id = st.sql_id
        ORDER BY 
            bt.blocking_level DESC, bt.sid
        
        """
    @staticmethod
    def get_locking():
        return """
            SELECT 
                do.object_name,
                lo.session_id,
                lo.inst_id,
                lo.oracle_username,
                lo.os_user_name,
                lo.process,
                lo.locked_mode
            FROM 
                gv$locked_object lo
                JOIN dba_objects do ON lo.object_id = do.object_id
            ORDER BY 
                lo.inst_id, lo.session_id
        """

    @staticmethod
    def get_trx():
        return """
        SELECT 
            s.inst_id,
            s.sid,
            s.serial#,
            s.username,
            s.status,
            s.machine,
            s.program,
            t.start_time,
            ROUND(SYSDATE - t.start_time, 2) * 24 * 60 AS duration_minutes,
            s.sql_id,
            sq.sql_text
        FROM 
            gv$transaction t
            JOIN gv$session s ON t.addr = s.taddr
            LEFT JOIN gv$sql sq ON s.sql_id = sq.sql_id AND sq.inst_id = s.inst_id
        WHERE 
            (SYSDATE - t.start_time) > INTERVAL '5' MINUTE 
        ORDER BY 
            duration_minutes DESC
        """

    @staticmethod
    def get_buffer_pool():
        return """
        SELECT 
            (1 - (phy.value / (cur.value + con.value))) * 100 AS buffer_hit_ratio
        FROM 
            v$sysstat cur, v$sysstat con, v$sysstat phy
        WHERE 
            cur.name = 'db block gets' 
            AND con.name = 'consistent gets' 
            AND phy.name = 'physical reads'
        """

    @staticmethod
    def get_tmp_table():
        return """
        SELECT 
            h.tablespace_name,
            ROUND(SUM(h.bytes_used) / 1024 / 1024, 2) AS used_mb,
            ROUND(SUM(h.bytes_free) / 1024 / 1024, 2) AS free_mb,
            ROUND(SUM(h.bytes_used + h.bytes_free) / 1024 / 1024, 2) AS total_mb,
            ROUND(
                (SUM(h.bytes_used) / GREATEST(SUM(h.bytes_used + h.bytes_free), 1)) * 100,
                2
            ) AS pct_used
        FROM 
            v$temp_space_header h
        GROUP BY 
            h.tablespace_name

        """

    @staticmethod
    def get_io_info():
        return """
        SELECT
            event,                                
            total_waits,
            time_waited * 10 AS time_waited_ms,   
            average_wait * 10 AS avg_wait_ms
        FROM
            v$system_event
        WHERE
            wait_class = 'User I/O'
        ORDER BY
            time_waited DESC
        """

    @staticmethod
    def get_sga_status():
        return """
        SELECT 
            pool,
            name,
            ROUND(bytes/1024/1024, 2) AS size_mb
        FROM 
            v$sgastat
        WHERE 
            name IN ('free memory')
            AND pool IN ('DEFAULT buffer cache', 'shared pool')
        ORDER BY 
            pool, bytes DESC
        """

    @staticmethod
    def get_pga_status():
        return """
        SELECT 
            name, 
            ROUND(value/1024/1024, 2) AS mb
        FROM 
            v$pgastat 
        WHERE 
            name IN (
                'aggregate PGA target parameter',
                'total PGA allocated',
                'total PGA used',
                'maximum PGA allocated',
                'global memory bound'
            )
        """

    @staticmethod
    def get_sga_total():
        return """
        SELECT * FROM v$sga
        """

    @staticmethod
    def get_table_size(database: str, table_names: List[str]):
        table_condition = "','".join(table_names)

        return f"""
        SELECT
            owner,
            segment_name AS "Table",
            ROUND(SUM(bytes) / 1024 / 1024, 2) AS "Size (MB)"
        FROM
            dba_segments
        WHERE
            segment_type = 'TABLE'
        AND segment_name IN ('{table_condition}')
        AND OWNER = '{database}'
        GROUP BY
            owner, segment_name
        ORDER BY
            SUM(bytes) DESC
        """
