"""Top-level data source abstraction layer.

Defines the Paradigm enum and DataSourceFactory abstract base class that
all data source factories (relational, KV, document, vector, etc.) inherit from.

All concrete factory subclasses with a non-empty ``name`` are automatically
collected into ``FactoryRegistry._pending`` via ``__init_subclass__``.
``datasource/__init__.py`` calls ``FactoryRegistry.register_pending()`` after
importing all paradigm packages to batch-register them.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import ClassVar

from datasource.registry import FactoryRegistry


class Paradigm(Enum):
    """Enumeration of data source paradigms.

    Each paradigm defines a distinct category of data source with its own
    tool set and operation semantics.
    """
    RELATIONAL = "relational"
    KV_STORE = "kv_store"
    DOCUMENT = "document"
    VECTOR = "vector"
    SEARCH_ENGINE = "search_engine"
    MESSAGE_QUEUE = "message_queue"


class DatabaseVersion(ABC):
    """Database version interface (all paradigms)."""

    @abstractmethod
    def get_db_version(self, pool_name: str) -> str:
        """Get database version string.

        Args:
            pool_name: Connection pool name.
        """
        pass


class DatabaseHealth(ABC):
    """Database health check interface (all paradigms)."""

    @abstractmethod
    def get_db_health(self, pool_name: str, health_type: str):
        """Get database health status.

        Args:
            pool_name: Connection pool name.
            health_type: Health check type.
        """
        pass

    def get_prompt(self, results: str, db_version: str, db_type: str = "") -> str:
        """Generate a diagnostic prompt for the health check results.

        Subclasses can override this to provide paradigm-specific
        diagnostic prompts. The default implementation returns a
        generic relational database prompt.

        Args:
            results: Health check results string.
            db_version: Database version string.
            db_type: Database type string (e.g. "mysql", "postgresql").

        Returns:
            Diagnostic prompt string.
        """
        return f"""# 角色
                你是一位精通各大主流数据库的专家，拥有超过15年的数据库问题分析处理经验,负责根据给定的数据库类型
                分析数据库的健康问题。
                你具备跨平台诊断能力，熟悉各大主流数据库的：
                - 内部运行机制（锁、事务、日志、缓存）
                - 性能监控视图与命令（如 performance_schema、pg_stat、v$session、DMVs 等）
                - 常见性能瓶颈与调优策略
                - 安全、连接、死锁、长事务、索引失效等问题的识别与修复

                # 背景
                - 数据库类型
                {db_type}

                - 数据库版本号
                {db_version}

                {results}

                # 任务
                - 仔细评估提供的数据库情况信息，并提供诊断报告和解决方案。

                # 分析要求（结构化输出）
                ## 数据库健康状态诊断报告
                -----
                ### 1.【数据库类型、版本信息】

                ### 2.【整体健康评估】
                - 判断当前是否存在严重问题（死锁、阻塞、连接耗尽、高延迟等）
                - 给出健康等级：🟢 健康 / 🟡 警告 / 🔴 严重】

                ### 3. 【分项诊断】
                按以下维度分析（仅输出存在的数据,若无提供对应的数据库情况信息，则需提示未提供分析的数据，无法进行分析，不要自己自行构造或推测）：
                - **连接问题**：连接数、失败连接、空闲连接过多等
                - **事务问题**：长事务、未提交事务、事务隔离级别
                - **锁与阻塞**：锁等待、死锁、表锁/行锁争用
                - **资源使用**：缓冲池命中率、临时表使用、磁盘 I/O、死元组、事务 ID 年龄、SGA内存、PGA内存使用情况等，根据数据返回的内容进行扩展分析

                ### 4. 【根因分析】
                结合数据库行为推断根本原因，例如：
                - 应用未提交事务
                - 缺少索引导致扫描
                - 配置不合理（如 max_connections、work_mem）
                - 锁粒度粗（如表锁替代行锁）

                ### 5. 【解决方案建议】
                提供**数据库类型专属**的可执行建议，格式：
                - ✅ **优化建议**：如"为 large_table 添加复合索引"
                - 💡 **SQL/命令示例**：使用对应数据库语法
                - ⚙️ **配置建议**：如 `work_mem = 64MB`（PG）、`innodb_buffer_pool_size`（MySQL）
                - 📊 **监控建议**：建议开启慢查询、设置告警

                ### 6. 【风险提示】
                - 标注操作风险等级（低/中/高）
                - 提示生产环境需备份、评估影响

                ## 输出要求
                - 使用清晰的 Markdown 结构
                - 所有建议必须基于输入数据，避免臆测
                - 若信息不足，请明确指出："需补充以下信息：..."
                - 对于 SQLite 等轻量数据库，说明其监控局限性"""


class DataSourceFactory(ABC):
    """Abstract base class for all data source factories.

    Every data source type (MySQL, Redis, MongoDB, etc.) must have a
    corresponding factory that inherits from this class. The factory
    declares its paradigm and provides methods to create operation handlers.

    Common operations (db_version, db_health) are defined here as they
    apply to all paradigms. Paradigm-specific operations are defined in
    subclasses (e.g., RelationalDataSourceFactory for relational databases).
    """

    name: str = ""
    paradigm: ClassVar[Paradigm] = Paradigm.RELATIONAL

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Collect concrete factories into the pending queue. Registration
        # is deferred to register_pending() to avoid import-order issues.
        if cls.name:
            FactoryRegistry.add_pending(cls)

    @classmethod
    def get_paradigm(cls) -> Paradigm:
        """Get the paradigm of this data source factory."""
        return cls.paradigm

    @abstractmethod
    def create_db_version(self) -> DatabaseVersion:
        """Create a database version handler.

        All paradigms support version querying, though the implementation
        differs (SQL VERSION() for relational, INFO for Redis, etc.).
        """
        ...

    @abstractmethod
    def create_db_health(self) -> DatabaseHealth:
        """Create a database health check handler.

        All paradigms support health checking, though the metrics and
        diagnostic commands differ by data source type.
        """
        ...

    def create_permission_policy(self):
        """Create a permission policy for this data source.

        Subclasses should override this to provide paradigm-specific
        permission checking. The default implementation raises
        ``NotImplementedError`` for paradigms that do not yet define
        a permission policy.

        Returns:
            A :class:`PermissionPolicy` instance.
        """
        raise NotImplementedError(
            f"Permission policy not implemented for data source '{self.name}'"
        )
