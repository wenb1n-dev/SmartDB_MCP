"""Redis key scanner handler.

Scans Redis keys by pattern using the SCAN command (non-blocking).
"""

from connection.pool_manager import MultiDBPoolManager


class RedisKeyScanner:
    """Scan Redis keys by pattern."""

    def scan_keys(
        self,
        pool_name: str,
        pattern: str = "*",
        count: int = 100,
    ) -> str:
        """Scan Redis keys matching a pattern.

        Uses SCAN (not KEYS) to avoid blocking the Redis server.

        Args:
            pool_name: Connection pool name.
            pattern: Key pattern (e.g., ``user:*``, ``session:*``).
            count: Hint for number of keys to return per SCAN iteration.

        Returns:
            Formatted key list string.
        """
        pool = MultiDBPoolManager.get_pool(pool_name)
        if pool is None:
            return f"错误: 连接池 '{pool_name}' 不存在"

        with pool.connection() as client:
            keys = []
            cursor = 0
            total_scanned = 0

            while True:
                cursor, batch = client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=count,
                )
                keys.extend(batch)
                total_scanned += 1

                if cursor == 0:
                    break

                # Safety limit: prevent infinite loops on very large keyspaces
                if len(keys) >= 10000:
                    keys = keys[:10000]
                    break

            if not keys:
                return f"未找到匹配 pattern '{pattern}' 的 Key"

            # Decode bytes keys
            decoded_keys = []
            for k in keys:
                if isinstance(k, bytes):
                    decoded_keys.append(k.decode("utf-8", errors="replace"))
                else:
                    decoded_keys.append(k)

            lines = [
                f"=== Key 扫描结果 ===",
                f"Pattern: {pattern}",
                f"匹配数量: {len(decoded_keys)}",
                f"扫描迭代次数: {total_scanned}",
                "",
            ]

            # Show first 100 keys
            display_keys = decoded_keys[:100]
            for k in display_keys:
                lines.append(f"  {k}")

            if len(decoded_keys) > 100:
                lines.append(f"  ... (仅显示前 100 个，共 {len(decoded_keys)} 个)")

            return "\n".join(lines)
