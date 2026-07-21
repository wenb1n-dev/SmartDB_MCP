"""Redis key info handler.

Queries key metadata: type, memory usage, TTL.
"""

from connection.pool_manager import MultiDBPoolManager


class RedisKeyInfo:
    """Query Redis key information."""

    def get_key_info(self, pool_name: str, key: str) -> str:
        """Get detailed information about a Redis key.

        Args:
            pool_name: Connection pool name.
            key: The Redis key to query.

        Returns:
            Formatted key info string.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        with pool.connection() as client:
            # Check if key exists
            exists = client.exists(key)
            if not exists:
                return f"Key '{key}' 不存在"

            # Get key type
            key_type = client.type(key)
            if isinstance(key_type, bytes):
                key_type = key_type.decode("utf-8", errors="replace")

            # Get TTL
            ttl = client.ttl(key)
            if ttl == -1:
                ttl_str = "永不过期"
            elif ttl == -2:
                ttl_str = "Key 不存在"
            else:
                ttl_str = f"{ttl} 秒"

            # Get memory usage
            try:
                mem_usage = client.memory_usage(key)
                if mem_usage is not None:
                    if mem_usage >= 1024 * 1024:
                        mem_str = f"{mem_usage / (1024 * 1024):.2f} MB"
                    elif mem_usage >= 1024:
                        mem_str = f"{mem_usage / 1024:.2f} KB"
                    else:
                        mem_str = f"{mem_usage} bytes"
                else:
                    mem_str = "N/A"
            except Exception:
                mem_str = "不支持"

            # Get size based on type
            size_str = self._get_type_size(client, key, key_type)

            lines = [
                f"=== Key 信息 ===",
                f"Key: {key}",
                f"Type: {key_type}",
                f"TTL: {ttl_str}",
                f"Memory Usage: {mem_str}",
                f"Size: {size_str}",
            ]

            return "\n".join(lines)

    def _get_type_size(self, client, key: str, key_type: str) -> str:
        """Get the size/count of a key based on its type."""
        try:
            if key_type == "string":
                length = client.strlen(key)
                return f"{length} bytes (string length)"
            elif key_type == "list":
                length = client.llen(key)
                return f"{length} elements (list)"
            elif key_type == "hash":
                length = client.hlen(key)
                return f"{length} fields (hash)"
            elif key_type == "set":
                length = client.scard(key)
                return f"{length} members (set)"
            elif key_type == "zset":
                length = client.zcard(key)
                return f"{length} members (zset)"
            elif key_type == "stream":
                length = client.xlen(key)
                return f"{length} entries (stream)"
            else:
                return "N/A"
        except Exception as e:
            return f"查询失败: {e}"
