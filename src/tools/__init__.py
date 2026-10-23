"""MCP 工具包入口。

工具按「通用 / 范式」分包存放，便于区分：

- common/：全范式通用工具（get_db_health / get_db_version）
- relational/：关系型（MySQL/PostgreSQL/Oracle/SQL Server/达梦）
- kv/：KV 存储（Redis）
- document/：文档型（MongoDB）
- vector/：向量型（Milvus）
- search_engine/：搜索引擎（Elasticsearch）
- message_queue/：消息队列（Kafka）

工具类继承 ToolsBase 后会在 __init_subclass__ 中自动注册到
ToolRegistry。本包被导入时（core.server 导入 tools.base 即会触发）
递归扫描所有子包并导入其中的模块，以完成注册；新增工具只需放入
对应范式子包，无需手动登记。
"""

import pkgutil

# 递归导入 tools 下所有模块（base.py 仅定义基类，无需导入）。
# 模块导入失败（如缺少可选驱动依赖）时跳过，不影响其他工具注册。
for _module in pkgutil.walk_packages(__path__, prefix=__name__ + "."):
    if _module.name == "tools.base":
        continue
    try:
        __import__(_module.name)
    except ImportError:
        pass

# 清理包命名空间，避免循环引用或命名污染
del pkgutil
