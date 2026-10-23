"""KV 存储范式工具（KV_STORE）。

适用于 Redis：
- execute_command：执行 Redis 命令
- get_key_info：查询 Key 详情（类型、TTL、内存占用）
- scan_keys：按 pattern 非阻塞扫描 Key
"""
