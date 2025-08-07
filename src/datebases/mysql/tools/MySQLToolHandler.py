from typing import Dict, Any
from sqlalchemy import text
from connection.MultiDBPoolManager import MultiDBPoolManager
from core.tools.ToolsBase import ToolsBase


class MySQLToolHandler(ToolsBase):
    def __init__(self):
        self.pool_manager = MultiDBPoolManager()
    
    def execute_sql(self, db_name: str, query: str) -> list:
        pool = self.pool_manager.get_pool(db_name)
        if not pool:
            raise ValueError(f"数据库连接池 '{db_name}' 不存在")
        
        with pool.connection() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()
            # 将结果转换为字符串列表
            if result.returns_rows:
                return [str(row) for row in rows]
            else:
                return [f"执行成功，影响行数: {result.rowcount}"]