from typing import List


class PostgresqlQueries:
    @staticmethod
    def get_db_version() -> str:
        """
        获取数据库版本的SQL查询

        Returns:
            SQL查询语句
        """
        return "SELECT version();"

    @staticmethod
    def get_table_names(schema: str, text: str) -> str:
        """
        根据注释获取表名的SQL查询

        Args:
            schema: 数据库名称
            text: 表注释关键词

        Returns:
            SQL查询语句
        """

        sql = f"""
        SELECT
            schemaname AS table_schema,
            tablename AS table_name,
            obj_description((schemaname || '.' || tablename)::regclass, 'pg_class') AS table_comment
        FROM
            pg_tables
        WHERE
            schemaname = '{ schema}'
        """

        if "SEARCH_ALL_TABLES" != text:
            sql += (
                f"AND( obj_description((schemaname || '.' || tablename)::regclass, 'pg_class') LIKE '%{text}%'"
                f"or tablename LIKE '%{text}%' )"
            )

        return sql

    @staticmethod
    def get_table_description(schema: str, table_names: List[str]) -> str:
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
                col.table_name AS "TABLE_NAME",
                col.column_name AS "COLUMN_NAME",
                pgd.description AS "COLUMN_COMMENT"
            FROM
                information_schema.columns col
                    LEFT JOIN
                pg_statio_all_tables stat ON stat.schemaname = col.table_schema
                    AND stat.relname = col.table_name
                    LEFT JOIN
                pg_class pgc ON pgc.oid = stat.relid
                    LEFT JOIN
                pg_description pgd ON pgd.objoid = pgc.oid
                    AND pgd.objsubid = col.ordinal_position
            WHERE
                col.table_schema = '{schema}'   
              AND col.table_name IN  ('{table_condition}')  
            ORDER BY
                col.table_name,
                col.ordinal_position;
                   """

    @staticmethod
    def get_table_index(schema: str, table_names: List[str]) -> str:
        table_condition = "','".join(table_names)

        return f"""
            SELECT
                t.relname AS TABLE_NAME,
                i.relname AS INDEX_NAME,
                a.attname AS COLUMN_NAME,
                (idx_positions.ordinality) AS SEQ_IN_INDEX,
                NOT ix.indisunique AS NON_UNIQUE,
                CASE
                    WHEN ix.indisprimary THEN 'PRIMARY'
                    WHEN ix.indisunique THEN 'UNIQUE'
                    ELSE 'NORMAL'
                    END AS INDEX_TYPE
            FROM
                pg_class t
                    JOIN
                pg_index ix ON t.oid = ix.indrelid
                    JOIN
                pg_class i ON i.oid = ix.indexrelid
                    JOIN
                pg_namespace n ON n.oid = t.relnamespace
                    JOIN
                LATERAL (
                    SELECT
                        UNNEST(ix.indkey::smallint[]) AS attnum,
                        generate_subscripts(ix.indkey, 1) AS ordinality
                    ) AS idx_positions ON true
                    JOIN
                pg_attribute a ON a.attrelid = t.oid AND a.attnum = idx_positions.attnum
            WHERE
                n.nspname = '{schema}'  
              AND t.relname IN ('{table_condition}') 
              AND t.relkind = 'r'   
            ORDER BY
                t.relname, i.relname, idx_positions.ordinality;
        """

    @staticmethod
    def get_max_connections() :
        return """
            SELECT 
            setting AS max_connections 
        FROM 
            pg_settings 
        WHERE 
            name = 'max_connections';
        """

    @staticmethod
    def get_current_connections(database: str) :
        return f"""
            SELECT 
              pid,
              usename,
              application_name,
              client_addr,
              backend_start,
              state,
              query,
              query_start,
              state_change
          FROM pg_stat_activity 
          WHERE datname = '{database}'
          ORDER BY backend_start;
        """

    @staticmethod
    def get_locking():
        return """
        SELECT 
            blocked_locks.pid     AS blocked_pid,
            blocked_activity.usename  AS blocked_user,
            blocking_locks.pid     AS blocking_pid,
            blocking_activity.usename AS blocking_user,
            blocked_activity.query    AS blocked_statement,
            blocking_activity.query   AS current_statement_in_blocking_process
        FROM 
            pg_catalog.pg_locks blocked_locks
        JOIN 
            pg_catalog.pg_stat_activity blocked_activity 
            ON blocked_activity.pid = blocked_locks.pid
        JOIN 
            pg_catalog.pg_locks blocking_locks 
            ON blocking_locks.locktype = blocked_locks.locktype
            AND blocking_locks.DATABASE IS NOT DISTINCT FROM blocked_locks.DATABASE
            AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
            AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
            AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
            AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
            AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
            AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
            AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
            AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
            AND blocking_locks.pid != blocked_locks.pid
        JOIN 
            pg_catalog.pg_stat_activity blocking_activity 
            ON blocking_activity.pid = blocking_locks.pid
        WHERE 
            NOT blocked_locks.GRANTED;
        """

    @staticmethod
    def get_buffer_pool():
        return """
        SELECT 
            SUM(blks_hit) * 100.0 / (SUM(blks_hit) + SUM(blks_read)) AS buffer_hit_ratio
        FROM 
            pg_stat_database 
        WHERE 
            datname = current_database();
        """

    @staticmethod
    def get_tmp_table():
        return """
        SELECT 
            temp_files, 
            temp_bytes 
        FROM 
            pg_stat_database 
        WHERE 
            datname = current_database();
        """
    @staticmethod
    def get_io_info():
        return """
        SELECT 
            datname AS database,
            blks_read,
            ROUND((blk_read_time / 1000.0)::NUMERIC, 2) AS read_time_s,
            ROUND((blk_write_time / 1000.0)::NUMERIC, 2) AS write_time_s,
            CASE 
                WHEN blks_read > 0 
                THEN ROUND((blk_read_time::NUMERIC / blks_read), 3)
                ELSE 0 
            END AS avg_read_latency_ms
        FROM 
            pg_stat_database
        WHERE 
            datname NOT LIKE 'template%'  
            AND datname IS NOT NULL
            AND blk_read_time IS NOT NULL
        ORDER BY 
            blk_read_time DESC;
        """
    @staticmethod
    def get_database_size():
        return """
            SELECT pg_size_pretty(pg_database_size(current_database())) AS database_size;
        """

    @staticmethod
    def get_table_top10():
        return """
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
            pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size
        FROM pg_tables
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        LIMIT 10;
        """

    @staticmethod
    def get_bgwriter_stats():
        return """
        SELECT 
            checkpoints_timed,
            checkpoints_req,
            checkpoint_write_time,
            checkpoint_sync_time,
            buffers_checkpoint,
            buffers_clean,
            buffers_backend,
            buffers_backend_fsync,
            buffers_alloc
        FROM pg_stat_bgwriter;
        """

    @staticmethod
    def get_dead_tup():
        return """
        SELECT 
          schemaname,
          relname,
          n_live_tup,
          n_dead_tup,
          last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze,
          (n_dead_tup::float/n_live_tup) AS dead_ratio,
          pg_size_pretty(pg_relation_size(schemaname||'.'||relname)) AS size
        FROM pg_stat_user_tables
        WHERE n_live_tup > 0
        ORDER BY dead_ratio DESC;
        """

    @staticmethod
    def get_mxid_age():
        return """
        SELECT
            datname,
            age(datfrozenxid)AS xid_age,
            mxid_age(datminmxid)AS mxid_age
        FROM
            pg_database
        WHERE
            datallowconn;
        """