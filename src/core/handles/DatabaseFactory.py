from config.dbconfig import get_db_configs, get_db_config_by_name
from core.tools.ToolsBase import ToolsBase
from datebases.mysql.tools.MySQLToolHandler import MySQLToolHandler

class DatabaseFactory:

    @classmethod
    def get_db_tool(cls, db_type: str) -> ToolsBase:
        print(f"正在使用数据库类型>>>: {db_type}")
        
        try:
            db_config = get_db_config_by_name(db_type)
        except ValueError:
            # 如果指定的数据库类型不存在，尝试使用默认配置
            configs = get_db_configs()
            if not configs:
                raise ValueError("没有找到任何数据库配置")
            # 使用第一个可用的配置
            first_key = list(configs.keys())[0]
            db_config = configs[first_key]
            print(f"使用默认数据库配置: {first_key}")

        if db_config["type"] == "mysql":
            return MySQLToolHandler()
        else:
            raise ValueError(f"不支持的数据库类型: {db_config['type']}")