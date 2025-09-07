from typing import List


class DamengQueries:
    @staticmethod
    def get_db_version() -> str:
        """
        获取数据库版本的SQL查询

        Returns:
            SQL查询语句
        """
        return "SELECT * FROM V$INSTANCE"

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
              SELECT A.COLUMN_NAME,
                A.DATA_TYPE,
                A.DATA_LENGTH,
                A.DATA_PRECISION,
                A.DATA_SCALE,
                A.NULLABLE,
                B.COMMENTS FROM ALL_TAB_COLUMNS A
            LEFT JOIN ALL_COL_COMMENTS B 
                ON A.TABLE_NAME = B.TABLE_NAME 
                AND A.COLUMN_NAME = B.COLUMN_NAME
            WHERE A.TABLE_NAME in ( '{table_condition}')
            AND B.SCHEMA_NAME = '{schema}'
               """

    @staticmethod
    def get_table_names(schema: str, text: str) -> str:
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
            OWNER           AS TABLE_SCHEMA,
            TABLE_NAME,
            COMMENTS        AS TABLE_COMMENT
        FROM 
            ALL_TAB_COMMENTS
        WHERE 
            OWNER = '{schema}'  
            AND TABLE_TYPE = 'TABLE'  
         """

        if "SEARCH_ALL_TABLES" != text:
            sql += f"AND ( COMMENTS LIKE '%{text}%' or TABLE_NAME LIKE '%{text}%'); "

        return sql

    @staticmethod
    def get_table_index(schema: str, table_names: List[str]):
        table_condition = "','".join(table_names)
        return f"""
            SELECT 
                A.TABLE_NAME,
                A.INDEX_NAME,
                A.COLUMN_NAME,
                A.COLUMN_POSITION AS SEQ_IN_INDEX,
                CASE 
                    WHEN B.UNIQUENESS = 'UNIQUE' THEN 0 
                    ELSE 1 
                END AS NON_UNIQUE,
                B.INDEX_TYPE
            FROM 
                ALL_IND_COLUMNS A
            JOIN 
                ALL_INDEXES B 
                ON A.INDEX_OWNER = B.OWNER 
                AND A.INDEX_NAME = B.INDEX_NAME
                AND A.TABLE_NAME = B.TABLE_NAME
            WHERE 
                A.INDEX_OWNER = '{schema}'           
                AND A.TABLE_NAME IN ('{table_condition}')
            ORDER BY 
                A.TABLE_NAME, 
                A.INDEX_NAME, 
                A.COLUMN_POSITION
        """

    @staticmethod
    def get_current_connections():
        return "SELECT * FROM V$SESSIONS"

    @staticmethod
    def get_active_session():
        return "SELECT * FROM V$SESSIONS WHERE STATE = 'ACTIVE';"

    @staticmethod
    def get_max_connections():
        return "SELECT PARA_VALUE AS MAX_SESSIONS FROM V$DM_INI WHERE PARA_NAME = 'MAX_SESSIONS';"


    @staticmethod
    def get_locking_session():
        return """
        SELECT 
            blocker.SESS_ID AS BLOCKER_SESS_ID,
            blocker.CLNT_IP AS BLOCKER_IP,
            blocker.USER_NAME AS BLOCKER_USER,
            blocker.SQL_TEXT AS BLOCKER_SQL,
            DBMS_LOB.SUBSTR(SF_GET_SESSION_SQL(blocker.SESS_ID)) AS BLOCKER_FULL_SQL,
            waiter.SESS_ID AS WAITER_SESS_ID,
            waiter.CLNT_IP AS WAITER_IP,
            waiter.USER_NAME AS WAITER_USER,
            waiter.SQL_TEXT AS WAITER_SQL,
            DBMS_LOB.SUBSTR(SF_GET_SESSION_SQL(waiter.SESS_ID)) AS WAITER_FULL_SQL,
            tab.NAME AS LOCKED_TABLE,
            lock.LTYPE AS LOCK_TYPE,        
            lock.LMODE AS LOCK_MODE,        
            lock.BLOCKED AS IS_BLOCKED      
        FROM V$TRXWAIT tw
        JOIN V$SESSIONS waiter ON tw.ID = waiter.TRX_ID           
        JOIN V$SESSIONS blocker ON tw.WAIT_FOR_ID = blocker.TRX_ID 
        JOIN V$LOCK lock ON waiter.TRX_ID = lock.TRX_ID AND lock.BLOCKED = 1
        JOIN SYSOBJECTS tab ON lock.TABLE_ID = tab.ID
        WHERE lock.BLOCKED = 1;
        """

    @staticmethod
    def get_lock_info():
        return """
        SELECT 
            s.CLNT_IP,
            s.USER_NAME,
            s.SQL_TEXT,
            l.LTYPE,
            l.LMODE,
            l.BLOCKED,
            o.NAME AS TABLE_NAME
        FROM V$LOCK l
        JOIN V$SESSIONS s ON l.TRX_ID = s.TRX_ID
        JOIN SYSOBJECTS o ON l.TABLE_ID = o.ID
        ORDER BY l.BLOCKED DESC, l.LMODE;
        """

    @staticmethod
    def get_buffer_pool():
        return """
        SELECT 
            NAME AS BUFFER_POOL_NAME,
            SUM(PAGE_SIZE) / 1024 AS BUFFER_POOL_SIZE_MB,
            SUM(RAT_HIT) / COUNT(*) AS HIT_RATIO
        FROM V$BUFFERPOOL 
        GROUP BY NAME;
        """

    @staticmethod
    def get_tmp_table():
        return """
        SELECT 
            DF.ID AS FILE_ID,
            DF.PATH AS FILE_PATH,
            DF.TOTAL_SIZE AS TOTAL_PAGES,
            DF.TOTAL_SIZE * DF.PAGE_SIZE / 1024 / 1024 AS TOTAL_SIZE_MB,
            DF.FREE_SIZE AS FREE_PAGES,
            DF.FREE_SIZE * DF.PAGE_SIZE / 1024 / 1024 AS FREE_SIZE_MB,
            (DF.TOTAL_SIZE - DF.FREE_SIZE) * DF.PAGE_SIZE / 1024 / 1024 AS USED_SIZE_MB,
            ROUND((DF.TOTAL_SIZE - DF.FREE_SIZE) / GREATEST(DF.TOTAL_SIZE, 1) * 100, 2) AS PCT_USED
        FROM V$DATAFILE DF
        JOIN V$TABLESPACE TS ON DF.GROUP_ID = TS.ID
        WHERE TS.NAME = 'TEMP';
        """

    @staticmethod
    def get_io_info():
        return """
        SELECT
            EVENT,
            TOTAL_WAITS,
            TIME_WAITED_MICRO / 1000 AS TIME_WAITED_MS,
            AVERAGE_WAIT_MICRO / 1000 AS AVG_WAIT_MS
        FROM V$SYSTEM_EVENT
        WHERE WAIT_CLASS = 'User I/O'
        ORDER BY TIME_WAITED DESC;
        """

    @staticmethod
    def get_sga_status():
        return """
        SELECT 
            NAME AS MEMORY_POOL,
            SUM(TOTAL_SIZE) / 1024 / 1024 AS TOTAL_SIZE_MB,
            SUM(DATA_SIZE) / 1024 / 1024 AS USED_SIZE_MB,
            SUM(RESERVED_SIZE) / 1024 / 1024 AS RESERVED_SIZE_MB
        FROM V$MEM_POOL
        GROUP BY NAME;
        """

    @staticmethod
    def get_pga_status():
        return """
        SELECT 
            NAME AS PGA_STAT_NAME,
            STAT_VAL AS PGA_VALUE
        FROM V$SYSSTAT
        WHERE NAME IN ('memory pool size in bytes', 'memory pool used bytes');
        """

    @staticmethod
    def get_sga_total():
        return """
        SELECT 
            NAME AS PARAMETER_NAME,
            VALUE AS PARAMETER_VALUE
        FROM V$PARAMETER
        WHERE NAME IN ('MEMORY_TARGET', 'MEMORY_POOL');
        """

    @staticmethod
    def get_table_space():
        return """
        SELECT 
            TS.NAME AS TABLESPACE_NAME,
            DF.TOTAL_SIZE * DF.PAGE_SIZE / 1024 / 1024 AS TOTAL_SIZE_MB,
            (DF.TOTAL_SIZE - DF.FREE_SIZE) * DF.PAGE_SIZE / 1024 / 1024 AS USED_SIZE_MB,
            DF.FREE_SIZE * DF.PAGE_SIZE / 1024 / 1024 AS FREE_SIZE_MB,
            ROUND((DF.TOTAL_SIZE - DF.FREE_SIZE) / DF.TOTAL_SIZE * 100, 2) AS USED_PERCENTAGE
        FROM V$TABLESPACE TS
        JOIN V$DATAFILE DF ON TS.ID = DF.GROUP_ID;
        """

    @staticmethod
    def get_table_size(schema: str, table_names: List[str]) -> str:
        table_condition = "','".join(table_names)

        return f"""
        SELECT 
            OWNER,
            SEGMENT_NAME AS "Table",
            ROUND(SUM(BYTES) / 1024 / 1024, 2) AS "Size (MB)"
        FROM 
            DBA_SEGMENTS
        WHERE 
            SEGMENT_TYPE = 'TABLE'
            AND SEGMENT_NAME IN ('{table_condition}')
            AND OWNER = '{schema}'
        GROUP BY 
            OWNER, SEGMENT_NAME
        ORDER BY 
            SUM(BYTES) DESC
        """