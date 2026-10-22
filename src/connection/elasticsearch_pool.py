"""Elasticsearch connection pool implementation.

Implements the :class:`ConnectionPool` ABC for Elasticsearch using the
official ``elasticsearch`` Python client (synchronous). Provides a unified
interface for acquiring ES connections within the SmartDB multi-paradigm gateway.
"""

import json
import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional, Tuple

import urllib3

from connection.base import ConnectionPool

logger = logging.getLogger(__name__)


def _probe_es_major_version(
    es_url: str,
    auth: Optional[Tuple[str, str]],
    use_ssl: bool,
    verify_certs: bool,
) -> Optional[int]:
    """探测 Elasticsearch 服务端的主版本号。

    官方 9.x 客户端会把所有请求的 Accept/Content-Type 头改写为
    ``application/vnd.elasticsearch+json; compatible-with=9``，而 8.x/7.x
    服务端只接受 ``compatible-with=8`` 或 ``7``，直接用 9.x 客户端连接会报
    400 ``media_type_header_exception``。

    因此在构造官方客户端之前，先用裸 HTTP 请求访问根路径 ``/`` 获取版本号。
    这里显式使用普通的 ``Accept: application/json``（不带 vnd/compatible-with），
    不会触发服务端的兼容版本校验，可稳定用于任意 7/8/9 版本。

    Args:
        es_url: Elasticsearch 根地址，如 ``http://127.0.0.1:9200``。
        auth: 可选的 (用户名, 密码) 元组。
        use_ssl: 是否使用 HTTPS。
        verify_certs: HTTPS 下是否校验证书。

    Returns:
        服务端主版本号（7/8/9）；探测失败时返回 None，由调用方保持客户端默认行为。
    """
    try:
        if use_ssl:
            cert_reqs = "CERT_REQUIRED" if verify_certs else "CERT_NONE"
            http = urllib3.PoolManager(cert_reqs=cert_reqs)
            if not verify_certs:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        else:
            http = urllib3.PoolManager()

        # 注意：使用普通 application/json，而非 vnd.elasticsearch+json，
        # 以绕过服务端对 compatible-with 版本号的强校验。
        headers = {"Accept": "application/json"}
        if auth:
            headers.update(urllib3.make_headers(basic_auth=f"{auth[0]}:{auth[1]}"))

        response = http.request(
            "GET",
            f"{es_url}/",
            headers=headers,
            timeout=5,
            retries=0,
        )
        if response.status != 200:
            logger.warning(
                f"探测 Elasticsearch 版本返回非 200 状态码: {response.status}"
            )
            return None

        payload = json.loads(response.data.decode("utf-8"))
        number = payload.get("version", {}).get("number", "")
        major = int(str(number).split(".")[0])
        logger.info(
            f"探测到 Elasticsearch 服务端主版本: {major} (完整版本: {number})"
        )
        return major
    except Exception as e:
        logger.warning(
            f"探测 Elasticsearch 版本失败，将保持客户端默认兼容版本: {e}"
        )
        return None


def _apply_client_compat_version(major: Optional[int]) -> None:
    """根据服务端主版本调整官方客户端发送的 compatible-with 版本号。

    elasticsearch-py 9.x 在模块加载时把兼容版本硬编码为客户端主版本 9（见
    ``elasticsearch._sync.client._base._COMPAT_MIMETYPE_TEMPLATE``），且每个请求
    的 Accept/Content-Type 都通过模块全局 ``_COMPAT_MIMETYPE_SUB`` 改写。
    此处重新绑定该模块全局变量，使同步客户端按目标服务端主版本（7/8）发送头，
    从而兼容旧版服务端。主版本为 9 或未知时不做改动。

    注意：该变量为进程级全局，单进程内多个不同主版本的 ES 实例会以最后一次
    设置为准；网关通常对接同版本集群，故此限制可接受。

    Args:
        major: 探测到的服务端主版本号；None 或 >=9 时不调整。
    """
    if major is None or major >= 9:
        return

    import elasticsearch._sync.client._base as es_base  # 同步客户端基础模块

    _patch_compat_template(es_base, major)


def _patch_compat_template(es_base: Any, major: int) -> None:
    """把同步客户端模块全局的 compatible-with 模板改写为指定主版本。

    抽出为独立函数，便于初始化探测与运行时自愈复用。

    Args:
        es_base: ``elasticsearch._sync.client._base`` 模块对象。
        major: 目标服务端主版本号（7/8）。
    """
    # 复刻官方模板，仅把尾部的主版本号替换为目标版本。
    template = "application/vnd.elasticsearch+%s; compatible-with=" + str(major)
    es_base._COMPAT_MIMETYPE_TEMPLATE = template
    # ``% (r"\g<1>",)`` 保留正则替换中对 mime 子类型（json/x-ndjson）的反向引用。
    es_base._COMPAT_MIMETYPE_SUB = template % (r"\g<1>",)
    logger.info(
        f"已将 elasticsearch 客户端兼容头版本调整为 compatible-with={major}"
    )


def _is_compat_version_error(exc: Exception) -> bool:
    """判断异常是否为服务端拒绝 compatible-with 版本号（media_type 400）。

    Args:
        exc: 调用 ES 时捕获的异常。

    Returns:
        是否为兼容版本不匹配错误。
    """
    message = str(exc).lower()
    return (
        "media_type_header_exception" in message
        or "compatible-with" in message
        or "invalid media-type" in message
    )


def _ensure_client_compatibility(
    client: Any, server_major: Optional[int]
) -> Optional[int]:
    """用真实客户端校验并自愈兼容头版本。

    流程：
    1. 直接 ``info()``，成功则说明当前兼容版本可用，直接返回探测到的主版本；
    2. 若报 media_type/compatible-with 400，则按候选主版本
       （优先探测结果，否则 8、7）依次改写模块全局模板并重试；
    3. 其他错误（网络、鉴权等）不做版本处理，避免掩盖真正问题。

    一旦某个版本 ``info()`` 成功，模块全局即被固定为该版本，后续所有
    复用同一客户端的工具都会带上正确的 compatible-with 头。

    Args:
        client: 已构造的 ``elasticsearch.Elasticsearch`` 同步客户端。
        server_major: 裸探测得到的主版本号，可能为 None。

    Returns:
        最终确定的服务端主版本号；无法确定时返回入参 ``server_major``。
    """
    import elasticsearch._sync.client._base as es_base

    # 候选版本：探测结果优先，其次 8、7（9 为客户端默认无需尝试）。
    candidates = []
    for m in (server_major, 8, 7):
        if m is not None and m < 9 and m not in candidates:
            candidates.append(m)

    try:
        # 先用当前已设置的兼容版本验证一次。
        info = client.info()
        number = info.get("version", {}).get("number", "")
        resolved = int(str(number).split(".")[0]) if number else server_major
        # 若 info 成功但探测版本与实际不符（例如探测失败默认 9），这里据实际校正。
        if resolved is not None and resolved < 9:
            _patch_compat_template(es_base, resolved)
        return resolved
    except Exception as exc:
        if not _is_compat_version_error(exc):
            # 非版本问题（网络、鉴权等），交给上层正常报错，不做改写。
            logger.warning(f"Elasticsearch info() 校验失败（非版本兼容问题）: {exc}")
            return server_major

        # 兼容版本被拒：按候选版本逐个改写并重试。
        for major in candidates:
            try:
                _patch_compat_template(es_base, major)
                client.info()
                logger.info(f"Elasticsearch 兼容版本自愈成功，锁定 compatible-with={major}")
                return major
            except Exception as retry_exc:
                if _is_compat_version_error(retry_exc):
                    continue
                logger.warning(
                    f"尝试 compatible-with={major} 时遇到非版本错误: {retry_exc}"
                )
                return major

        logger.error("Elasticsearch 兼容版本自适应失败：候选版本均被拒绝")
        return server_major


class ElasticsearchConnectionPool(ConnectionPool):
    """Elasticsearch connection pool backed by ``elasticsearch``.

    Uses ``elasticsearch.Elasticsearch`` which is thread-safe and manages
    a connection pool internally via the ``urllib3`` transport layer.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9200,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        use_ssl: bool = False,
        verify_certs: bool = True,
        pool_size: int = 10,
        **kwargs,
    ):
        """Initialize the Elasticsearch connection pool.

        Args:
            host: ES server host.
            port: ES server port (default: 9200).
            user: ES username (optional if no auth).
            password: ES password (optional if no auth).
            database: Not used for ES (kept for interface compatibility).
            use_ssl: Whether to use HTTPS.
            verify_certs: Whether to verify SSL certificates.
            pool_size: Maximum connections in the pool.
        """
        from elasticsearch import Elasticsearch

        self.host = host
        self.port = port
        self.max_pool_size = pool_size

        # Build connection params
        scheme = "https" if use_ssl else "http"
        es_url = f"{scheme}://{host}:{port}"

        es_kwargs = {
            "hosts": [es_url],
            "request_timeout": 30,
            "max_retries": 3,
            "retry_on_timeout": True,
        }

        if use_ssl:
            es_kwargs["verify_certs"] = verify_certs
            es_kwargs["ssl_show_warn"] = False

        if user and password:
            es_kwargs["basic_auth"] = (user, password)

        # 版本兼容处理：先裸探测服务端主版本，再调整 9.x 客户端发送的
        # compatible-with 头，避免连接 8.x/7.x 服务端时报 400 media_type_header_exception。
        auth_tuple = (user, password) if user and password else None
        server_major = _probe_es_major_version(
            es_url, auth_tuple, use_ssl, verify_certs
        )
        _apply_client_compat_version(server_major)

        self._client = Elasticsearch(**es_kwargs)

        # 自愈校验：裸探测可能因鉴权/代理等原因失败（返回 None，兼容版本未调整）。
        # 这里用真实客户端调用 info() 验证；若仍因 compatible-with 版本被拒，
        # 则按服务端主版本（优先探测结果，否则依次尝试 8、7）切换并重试，
        # 确保 search/indices/mapping 等所有走同一客户端的工具版本头一致。
        self._server_major = _ensure_client_compatibility(
            self._client, server_major
        )

        logger.info(
            f"Elasticsearch connection pool initialized for {host}:{port}"
            f" ssl={use_ssl} server_major={self._server_major}"
        )

    def get_connection(self) -> Any:
        """Acquire the Elasticsearch client instance.

        Returns the :class:`Elasticsearch` instance. The client is
        thread-safe and shared across all callers.
        """
        logger.debug("Elasticsearch client acquired")
        return self._client

    def return_connection(self, conn: Any) -> None:
        """Return an ES connection to the pool.

        The ``elasticsearch`` client manages connections internally.
        This is a no-op wrapper to satisfy the :class:`ConnectionPool`
        interface.
        """
        logger.debug("Elasticsearch connection returned to pool")

    @contextmanager
    def connection(self) -> Iterator[Any]:
        """Context manager for acquiring an Elasticsearch client.

        Usage::

            with pool.connection() as client:
                info = client.info()
        """
        client = self.get_connection()
        try:
            yield client
        finally:
            self.return_connection(client)

    def get_stats(self) -> Dict[str, Any]:
        """Get Elasticsearch connection pool statistics."""
        stats = {
            "pool_type": "elasticsearch",
            "host": self.host,
            "port": self.port,
            "max_pool_size": self.max_pool_size,
        }
        try:
            info = self._client.info()
            version = info.get("version", {}).get("number", "unknown")
            stats["server_version"] = version
        except Exception:
            stats["server_version"] = "unavailable"
        return stats

    def close_all_connections(self) -> None:
        """Close all connections in the ES pool."""
        try:
            self._client.close()
            logger.info("All Elasticsearch connections closed")
        except Exception as e:
            logger.error(f"Error closing Elasticsearch connections: {e}")
