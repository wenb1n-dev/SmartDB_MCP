import os
import json
from typing import Dict, List, Any

def get_db_configs() -> Dict[str, Dict[str, Any]]:
    """从环境变量或配置文件获取多个数据库配置信息

    返回:
        dict: 包含多个数据库连接配置的字典
        格式: {
            "db1": {
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "password",
                "database": "test_db1",
                "role": "readonly",
                "pool_size": 10,
                "max_overflow": 20,
                "pool_recycle": 3600,
                "pool_timeout": 30
            },
            "db2": { ... }
        }

    异常:
        ValueError: 当必需的配置信息缺失时抛出
    """
    # 加载.env文件
    #load_dotenv()

    # 优先从配置文件读取
    config_file = os.getenv("DATABASE_CONFIG_FILE", os.path.join(os.path.dirname(__file__), "database_config.json"))

    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                db_configs = json.load(f)
                return _validate_db_configs(db_configs)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: 无法读取配置文件 {config_file}: {e}")
    
    # 从环境变量获取数据库配置
    db_configs_str = os.getenv("DATABASE_CONFIGS", "")
    
    if db_configs_str:
        try:
            db_configs = json.loads(db_configs_str)
            return _validate_db_configs(db_configs)
        except json.JSONDecodeError as e:
            raise ValueError(f"DATABASE_CONFIGS 格式错误: {e}")
    
    # 如果没有配置，返回空字典
    return {}

def _validate_db_configs(db_configs: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """验证数据库配置的完整性"""
    validated_configs = {}
    
    for db_name, config in db_configs.items():
        # 设置默认值
        validated_config = {
            "host": config.get("host", "localhost"),
            "port": int(config.get("port", "3306")),
            "user": config.get("user"),
            "password": config.get("password"),
            "database": config.get("database"),
            "role": config.get("role", "readonly"),
            "pool_size": int(config.get("pool_size", "10")),
            "max_overflow": int(config.get("max_overflow", "20")),
            "pool_recycle": int(config.get("pool_recycle", "3600")),
            "pool_timeout": int(config.get("pool_timeout", "30")),
            "type": config.get("type"),
            "schema": config.get("schema"),
            "service_name": config.get("service_name")
        }
        
        # 验证必需字段
        if not all([validated_config["user"], validated_config["password"], validated_config["database"]]):
            raise ValueError(f"数据库 '{db_name}' 缺少必需的配置信息")
        
        validated_configs[db_name] = validated_config
    
    return validated_configs

def get_db_config() -> Dict[str, Any]:
    """获取默认数据库配置（向后兼容）"""
    configs = get_db_configs()
    if not configs:
        raise ValueError("没有找到数据库配置")
    elif len(configs) == 1:
        return list(configs.values())[0]
    else:
        # 如果有多个配置，返回第一个
        first_key = list(configs.keys())[0]
        return configs[first_key]

def get_db_config_by_name(db_name: str) -> Dict[str, Any]:
    """根据数据库名称获取特定配置"""
    configs = get_db_configs()
    if db_name not in configs:
        raise ValueError(f"数据库配置 '{db_name}' 不存在")
    return configs[db_name]

# 定义角色权限
ROLE_PERMISSIONS = {
    "readonly": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"],  # 只读权限
    "writer": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE"],  # 读写权限
    "admin": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE", 
             "CREATE", "ALTER", "DROP", "TRUNCATE"]  # 管理员权限
}

def get_role_permissions(role: str) -> list:
    """获取指定角色的权限列表
    
    参数:
        role (str): 角色名称
        
    返回:
        list: 该角色允许执行的SQL操作列表
    """
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["readonly"])  # 默认返回只读权限