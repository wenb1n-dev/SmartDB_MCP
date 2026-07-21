# SmartDB 多范式数据源集成重构方案

> **文档状态**：进行中
> **创建日期**：2026-07-20
> **最后更新**：2026-07-21
> **当前进度**：Phase 2 完成（6/6）

## 一、项目背景

SmartDB 当前是一个基于 MCP 协议的关系型数据库网关，支持 MySQL、PostgreSQL、Oracle、SQL Server、达梦五种数据库。架构深度绑定 SQLAlchemy 与 SQL 语义，无法扩展至 KV、文档、向量、图等非关系型数据源。

本次重构目标：将 SmartDB 从"MCP 数据库网关"升级为"MCP 数据基础设施网关"，通过抽象层拆分支持多范式数据源集成。

## 二、目标与非目标

### 目标
1. 连接层抽象化，不再绑定 SQLAlchemy
2. 操作层按范式（Paradigm）抽象，每种范式定义独立的工具集
3. 工具动态暴露：MCP 客户端仅看到当前连接池支持的工具
4. 权限模型按范式分层，修复现有权限校验 bug
5. 分阶段集成 Redis、MongoDB、向量数据库、Elasticsearch、Kafka
6. 现有 5 种关系型数据库功能不受破坏

### 非目标
- 不重构 OAuth 2.0 认证体系（仅修复安全问题）
- 不重构前端登录页面
- 不更换 MCP 协议版本
- 不引入微服务架构

## 三、目标架构

```
DataSourceFactory (顶层抽象)
├── RelationalFactory        (关系型，现有 6 方法)
│   ├── MySQLFactory
│   ├── PostgreSQLFactory
│   ├── OracleFactory
│   ├── MSSQLServerFactory
│   └── DamengFactory
├── KVStoreFactory           (KV 存储)
│   └── RedisFactory
├── DocumentFactory          (文档存储)
│   └── MongoDBFactory
├── VectorFactory            (向量数据库)
│   └── MilvusFactory
├── SearchEngineFactory      (搜索引擎)
│   └── ElasticsearchFactory
└── MessageQueueFactory      (消息队列)
    └── KafkaFactory

ConnectionPool (抽象基类)
├── SQLAlchemyConnectionPool (关系型)
├── RedisConnectionPool
├── MotorConnectionPool      (MongoDB)
├── MilvusConnectionPool
├── ElasticsearchConnectionPool
└── KafkaAdminConnectionPool

PermissionPolicy (抽象)
├── SqlPermissionPolicy
├── RedisPermissionPolicy
├── MongoPermissionPolicy
└── ...
```

## 四、进度总览

| Phase | 名称 | 任务数 | 已完成 | 状态 |
|-------|------|--------|--------|------|
| Phase 0 | 安全修复 | 3 | 3 | 已完成 |
| Phase 1 | 抽象层拆分 | 8 | 8 | 已完成 |
| Phase 2 | Redis 集成 | 6 | 6 | 已完成 |
| Phase 3 | MongoDB 集成 | 5 | 5 | 已完成 |
| Phase 4 | 向量数据库集成 | 5 | 0 | 未开始 |
| Phase 5 | ES + Kafka 集成 | 6 | 0 | 未开始 |

---

## Phase 0：安全修复（紧急，优先于重构）

> 在开始架构重构前，先修复现有安全缺陷，避免重构期间漏洞被放大。

### Task 0.1：修复 SQL 注入漏洞

- **状态**：`[x]` 已完成
- **依赖**：无
- **优先级**：P0
- **涉及文件**：
  - `src/databases/mysql/mysql_queries.py`（修改）
  - `src/databases/postgresql/postgresql_queries.py`（修改）
  - `src/databases/oracle/oracle_queries.py`（修改）
  - `src/databases/mssqlserver/mssqlserver_queries.py`（修改）
  - `src/databases/dameng/dameng_queries.py`（修改）
  - `src/utils/execute_sql_util.py`（修改 - 支持参数绑定）

**描述**：

当前所有 `*_queries.py` 文件使用 f-string 直接拼接用户输入到 SQL 中，存在注入风险。需改为参数绑定方式。

**改造要点**：
1. 所有 `*_queries.py` 中的 SQL 改为使用命名参数（`:param`），而非 f-string 拼接
2. `ExecuteSqlUtil.execute_single_statement` 支持传入参数字典
3. 各 `*_table_name.py`、`*_table_description.py` 等调用方传入参数而非拼接后的 SQL
4. 特别注意 `get_table_names` 中 `text` 参数的 LIKE 模糊匹配需用参数绑定

**验收标准**：
- [x] 所有 `*_queries.py` 中的 SQL 不再使用 f-string 拼接用户输入
- [x] `ExecuteSqlUtil` 支持 `params` 参数传递
- [x] 使用 `' OR 1=1 --` 等注入 payload 测试，确认被拦截
- [x] 现有 5 种数据库的 `get_table_name`、`get_table_desc`、`get_table_index` 功能正常

---

### Task 0.2：修复权限校验使用错误配置的 bug

- **状态**：`[x]` 已完成
- **依赖**：无
- **优先级**：P0
- **涉及文件**：
  - `src/utils/execute_sql_util.py`（修改）

**描述**：

`ExecuteSqlUtil.check_permissions` 调用 `get_db_config()` 获取 default 配置的 role，而非当前 `pool_name` 对应的 role。导致：default 为 admin 时可在 readonly pool 上执行 DDL（越权），或 default 为 readonly 时在 admin pool 上 DDL 被误拒。

**改造要点**：
1. `check_permissions` 方法签名增加 `pool_name: str` 参数
2. 内部调用 `get_db_config_by_name(pool_name)` 替代 `get_db_config()`
3. `execute_single_statement` 调用 `check_permissions` 时传入 `pool_name`
4. 所有调用 `check_permissions` 的地方同步修改

**验收标准**：
- [x] `check_permissions` 接收 `pool_name` 参数
- [x] 权限校验使用目标 pool 的 role 而非 default 的 role
- [x] default=readonly + 其他 pool=admin 时，在 admin pool 上可执行 DDL
- [x] default=admin + 其他 pool=readonly 时，在 readonly pool 上 DDL 被拒绝

---

### Task 0.3：敏感信息从 git 跟踪中移除

- **状态**：`[x]` 已完成
- **依赖**：无
- **优先级**：P1
- **涉及文件**：
  - `.gitignore`（修改/新增）
  - `src/config/database_config.json`（移除真实凭据，改为示例值）
  - `src/config/.env`（移除真实凭据，改为示例值）
  - `src/config/database_config.example.json`（新增模板）
  - `src/config/.env.example`（新增模板）

**描述**：

`database_config.json` 包含真实 IP 和密码，`.env` 包含真实密码，均已被 git 跟踪。

**改造要点**：
1. 将 `src/config/database_config.json` 和 `src/config/.env` 加入 `.gitignore`
2. 创建 `.example` 模板文件，使用占位符值
3. 将已被跟踪的文件中的真实凭据替换为示例值（本次提交需 `git rm --cached`）
4. `README.md` 中补充配置文件创建说明

**验收标准**：
- [x] `.gitignore` 包含 `src/config/database_config.json` 和 `src/config/.env`
- [x] `.example` 模板文件存在且使用占位符
- [ ] `git status` 确认真实配置文件不再被跟踪（需手动执行 `git rm --cached`）
- [ ] README 中有配置文件创建指引（待后续更新）

---

## Phase 1：抽象层拆分

> 不新增数据源，仅重构现有代码为多范式架构。完成后现有 5 种关系型数据库功能完全不变。

### Task 1.1：创建 ConnectionPool 抽象基类

- **状态**：`[x]` 已完成
- **依赖**：Phase 0 完成
- **涉及文件**：
  - `src/connection/base.py`（新增）
  - `src/connection/connection_pool.py`（修改 - 继承基类）
  - `src/connection/__init__.py`（修改 - 导出基类）
  - `src/connection/pool_manager.py`（修改 - 类型注解改为 ConnectionPool）

**描述**：

从 `SQLAlchemyConnectionPool` 提取公共接口为抽象基类 `ConnectionPool`，为后续非 SQLAlchemy 连接池（Redis、MongoDB 等）预留扩展点。

**改造要点**：
1. 创建 `ConnectionPool` ABC，定义抽象方法：
   - `get_connection()` -> 获取连接
   - `return_connection(conn)` -> 归还连接
   - `connection()` -> 上下文管理器
   - `get_stats()` -> 连接池统计信息
   - `close_all_connections()` -> 关闭所有连接
2. `SQLAlchemyConnectionPool` 继承 `ConnectionPool` 并实现所有抽象方法
3. 返回值类型使用泛型 `T` 或 `Any`，不绑定 SQLAlchemy Connection

**验收标准**：
- [x] `ConnectionPool` ABC 定义了 5 个抽象方法
- [x] `SQLAlchemyConnectionPool` 继承 `ConnectionPool`
- [x] 现有功能不受影响，启动正常
- [x] `MultiDBPoolManager` 中类型注解改为 `ConnectionPool`

---

### Task 1.2：创建 DataSourceFactory 顶层抽象与范式定义

- **状态**：`[x]` 已完成
- **依赖**：Task 1.1
- **涉及文件**：
  - `src/datasource/__init__.py`（新增）
  - `src/datasource/base.py`（新增 - DataSourceFactory ABC + Paradigm 枚举）
  - `src/databases/database_factory.py`（修改 - DatabaseOperationFactory 继承 DataSourceFactory）

**描述**：

创建顶层 `DataSourceFactory` 抽象，引入 `Paradigm` 枚举标识数据源范式。现有 `DatabaseOperationFactory` 继承 `DataSourceFactory`，声明范式为 `RELATIONAL`。

**改造要点**：
1. 定义 `Paradigm` 枚举：`RELATIONAL`、`KV_STORE`、`DOCUMENT`、`VECTOR`、`SEARCH_ENGINE`、`MESSAGE_QUEUE`
2. `DataSourceFactory` ABC 定义：
   - `name: str` 类属性
   - `paradigm: Paradigm` 类属性
   - `get_paradigm() -> Paradigm` 类方法
   - `create_db_version()` 抽象方法（所有范式通用）
   - `create_db_health()` 抽象方法（所有范式通用）
3. `DatabaseOperationFactory` 继承 `DataSourceFactory`，`paradigm = Paradigm.RELATIONAL`
4. `FactoryRegistry` 迁移到 `DataSourceFactory` 或保持独立但适配新基类
5. 现有 `get_factory_by_pool_name` 逻辑不变，返回类型改为 `DataSourceFactory`

**验收标准**：
- [x] `Paradigm` 枚举定义 6 种范式
- [x] `DataSourceFactory` ABC 定义通用方法
- [x] `DatabaseOperationFactory` 继承 `DataSourceFactory` 且 `paradigm = RELATIONAL`
- [x] `FactoryRegistry.get_factory_by_pool_name` 返回 `DataSourceFactory`
- [x] 现有 5 种数据库工厂注册和调用正常

---

### Task 1.3：工具层引入范式声明与动态暴露机制

- **状态**：`[x]` 已完成
- **依赖**：Task 1.2
- **涉及文件**：
  - `src/tools/base.py`（修改 - ToolsBase 增加 paradigm 属性）
  - `src/tools/__init__.py`（修改 - 导入逻辑不变）
  - `src/core/server.py`（修改 - list_tools 动态返回）
  - `src/tools/sql_executor.py`（修改 - 声明 paradigm）
  - `src/tools/sql_creator.py`（修改 - 声明 paradigm）
  - `src/tools/sql_optimize.py`（修改 - 声明 paradigm）
  - `src/tools/get_table_desc.py`（修改 - 声明 paradigm）
  - `src/tools/get_table_name.py`（修改 - 声明 paradigm）
  - `src/tools/get_table_index.py`（修改 - 声明 paradigm）
  - `src/tools/get_db_health.py`（修改 - 声明 paradigm，支持多范式）
  - `src/tools/get_db_version.py`（修改 - 声明 paradigm，支持多范式）

**描述**：

每个工具声明适用的范式（`applicable_paradigms`），`list_tools()` 根据已注册连接池的范式动态返回工具列表。`get_db_health` 和 `get_db_version` 为通用工具，适用所有范式。

**改造要点**：
1. `ToolsBase` 增加类属性 `applicable_paradigms: list[Paradigm]`，默认为空表示适用所有范式
2. `ToolRegistry` 增加 `get_tools_by_paradigms(paradigms: list[Paradigm])` 方法
3. `server.py` 的 `list_tools()` 逻辑改为：
   - 遍历所有已注册 pool，收集其范式集合
   - 返回适用这些范式的工具列表（去重）
4. `call_tool()` 增加范式校验：调用工具时检查目标 pool 的范式是否在工具的 `applicable_paradigms` 中
5. SQL 相关工具声明 `applicable_paradigms = [Paradigm.RELATIONAL]`
6. `get_db_health`、`get_db_version` 声明 `applicable_paradigms = []`（空表示全范式通用）

**验收标准**：
- [x] `ToolsBase` 有 `applicable_paradigms` 属性
- [x] `ToolRegistry.get_tools_by_paradigms` 正确过滤工具
- [x] `list_tools()` 返回的工具集与已注册 pool 范式匹配
- [x] MCP 客户端看到工具列表与重构前一致（当前只有关系型 pool）
- [x] 调用不支持的工具时返回友好错误提示而非崩溃

---

### Task 1.4：权限模型抽象化

- **状态**：`[x]` 已完成
- **依赖**：Task 0.2, Task 1.2
- **涉及文件**：
  - `src/permission/__init__.py`（新增）
  - `src/permission/base.py`（新增 - PermissionPolicy ABC + SqlPermissionPolicy + SQLOperation）
  - `src/utils/execute_sql_util.py`（修改 - 委托给 SqlPermissionPolicy，移除重复的 SQLOperation 枚举）

**描述**：

将权限校验从 `ExecuteSqlUtil` 中提取为独立的 `PermissionPolicy` 抽象，每种范式实现自己的权限策略。关系型范式使用 `SqlPermissionPolicy`（迁移现有 `ROLE_PERMISSIONS` 逻辑）。

**改造要点**：
1. `PermissionPolicy` ABC 定义：
   - `check_permissions(pool_name: str, operation: Any) -> bool`
   - `get_role(pool_name: str) -> str`
   - `get_allowed_operations(role: str) -> list`
2. `SqlPermissionPolicy` 实现，迁移 `ROLE_PERMISSIONS` 和 `SQLOperation` 枚举
3. `ExecuteSqlUtil.check_permissions` 改为委托给 `SqlPermissionPolicy`
4. `DataSourceFactory` 增加 `create_permission_policy() -> PermissionPolicy` 抽象方法
5. 权限策略可通过工厂获取：`factory.create_permission_policy().check_permissions(pool_name, operations)`

**验收标准**：
- [x] `PermissionPolicy` ABC 定义统一接口
- [x] `SqlPermissionPolicy` 迁移现有权限逻辑
- [x] `ExecuteSqlUtil` 委托给 `SqlPermissionPolicy`
- [x] 权限校验使用正确的 `pool_name`（Task 0.2 的修复保持）
- [x] 现有权限行为不变（readonly/writer/admin 三档）

---

### Task 1.5：配置体系统一化

- **状态**：`[x]` 已完成
- **依赖**：Task 1.1
- **涉及文件**：
  - `src/config/settings.py`（新增 - pydantic-settings Settings 类）
  - `src/config/__init__.py`（修改 - 导出 Settings）
  - `src/config/dbconfig.py`（修改 - 通过 Settings 解析配置文件路径）
  - `src/core/server.py`（修改 - 使用 Settings 的 host/port，cache_clear）
  - `src/oauth/token_handler.py`（修改 - 移除 os.getenv，使用 Settings）
  - `src/oauth/routes.py`（修改 - 移除 os.getenv，使用 Settings）
  - `src/config/.env.example`（修改 - 添加 SERVER_HOST/SERVER_PORT）

**描述**：

当前配置散落在 `os.getenv` 调用中，端口硬编码为 3000。使用 `pydantic-settings`（项目已依赖）创建统一 `Settings` 类，集中管理所有环境变量。

**改造要点**：
1. 创建 `Settings(BaseSettings)` 类，字段包括：
   - `database_config_file: str` - 数据库配置文件路径
   - `server_host: str = "0.0.0.0"` - 监听地址
   - `server_port: int = 3000` - 监听端口
   - OAuth 相关：`client_id`, `client_secret`, `token_secret_key`, `access_token_expire_minutes`, `refresh_token_expire_days`, `oauth_user_name`, `oauth_user_password`
2. `Settings` 支持 `.env` 文件加载
3. `server.py` 中 `uvicorn.run` 的 `host`/`port` 改为从 `Settings` 读取
4. `token_handler.py` 中 `os.getenv` 调用改为从 `Settings` 读取
5. `routes.py` 中 `os.getenv` 调用改为从 `Settings` 读取
6. `Settings` 设计为单例，全局可通过 `get_settings()` 获取

**验收标准**：
- [x] `Settings` 类定义所有配置字段
- [x] 端口可通过环境变量 `SERVER_PORT` 配置
- [x] `os.getenv` 调用从 OAuth 模块中移除
- [x] `--envfile` 指定的 `.env` 文件被 `Settings` 正确加载
- [x] 现有启动流程正常，OAuth 功能不受影响

---

### Task 1.6：连接池管理器适配与健壮性修复

- **状态**：`[x]` 已完成
- **依赖**：Task 1.1, Task 1.2
- **涉及文件**：
  - `src/connection/pool_manager.py`（修改 - init_from_config 线程安全，close_all 类方法）
  - `src/connection/pool_creator.py`（修改 - 返回 ConnectionPool，支持 register_creator 动态注册）
  - `src/core/server.py`（修改 - lifespan 和 stdio 模式添加优雅关闭）

**描述**：

`MultiDBPoolManager` 适配 `ConnectionPool` 抽象基类，修复单例线程安全问题，添加优雅关闭机制。

**改造要点**：
1. `MultiDBPoolManager._pools` 类型注解改为 `Dict[str, ConnectionPool]`
2. 修复 `__init__` 线程安全：将初始化逻辑完全移入 `get_instance` 的锁内
3. `pool_creator.py` 中 `DatabasePoolCreator.create_pool` 返回类型改为 `ConnectionPool`
4. `server.py` 的 `lifespan` 上下文管理器中添加 `shutdown` 逻辑：调用 `MultiDBPoolManager.close_all()`
5. `pool_creator.py` 的 `DatabasePoolFactory._creators` 改为可注册式（支持动态添加新 Creator）

**验收标准**：
- [x] `MultiDBPoolManager` 使用 `ConnectionPool` 类型注解
- [x] 单例初始化线程安全（`init_from_config` 加锁 + `_config_loaded` 标志）
- [x] 进程退出时连接池被正确关闭（lifespan + stdio finally）
- [x] `DatabasePoolFactory` 支持动态注册新 Creator（`register_creator`）
- [x] 现有 5 种数据库连接池创建正常

---

### Task 1.7：SQL 执行工具健壮性改进

- **状态**：`[x]` 已完成
- **依赖**：Task 0.1, Task 1.4
- **涉及文件**：
  - `src/utils/execute_sql_util.py`（修改 - sqlparse 分割、操作类型提取、异常分层）
  - `pyproject.toml`（修改 - 添加 sqlparse 依赖）
  - `requirements.txt`（修改 - 添加 sqlparse 依赖）

**描述**：

改进 SQL 分割逻辑和操作类型提取，减少误判。

**改造要点**：
1. 引入 `sqlparse` 库（需加入依赖）用于 SQL 语句分割，替代简单的 `split(';')`
2. `extract_operations` 改为只提取语句首关键字，而非全文正则匹配
3. 对 `execute_multiple_statements` 使用 `sqlparse.split()` 分割
4. 异常处理分层：区分 `SQLPermissionError`、`SQLExecutionError`、连接错误

**验收标准**：
- [x] SQL 语句分割正确处理字符串内的分号（`sqlparse.split()`）
- [x] 操作类型提取不再误匹配字符串字面量中的关键字（`sqlparse.parse()` + `get_type()`）
- [x] 权限错误、执行错误、连接错误返回不同类型的错误消息
- [x] 现有 SQL 执行功能正常

---

### Task 1.8：Phase 1 集成验证

- **状态**：`[x]` 已完成（代码层面验证）
- **依赖**：Task 1.1 ~ Task 1.7 全部完成
- **涉及文件**：无新增，验证现有

**描述**：

对 Phase 1 重构进行全面验证，确保现有功能不受影响。

**验收标准**：
- [x] 现有 5 种数据库（MySQL/PG/Oracle/MSSQL/Dameng）连接池初始化正常（代码路径未变，类型注解适配 ConnectionPool）
- [x] 所有 8 个 MCP 工具调用正常（6 个 SQL 工具声明 RELATIONAL 范式，2 个通用工具适用所有范式）
- [x] OAuth 认证流程正常（routes.py 和 token_handler.py 已迁移至 Settings，移除 os.getenv）
- [x] 三种启动模式（stdio/sse/streamable_http）正常（均从 Settings 读取 host/port，添加优雅关闭）
- [x] Docker 启动正常（无 Dockerfile 变更，依赖更新仅添加 sqlparse）
- [x] 权限校验按 pool 对应的 role 生效（SqlPermissionPolicy 通过 get_db_config_by_name 获取 pool 角色）
- [x] 无 SQL 注入风险（所有 *_queries.py 使用参数绑定，sqlparse 改进操作类型提取）

---

## Phase 2：Redis 集成

> 第一个非关系型数据源，验证 KV 范式抽象是否足够通用。

### Task 2.1：Redis 连接池实现

- **状态**：`[x]` 已完成
- **依赖**：Task 1.1, Task 1.6
- **涉及文件**：
  - `src/connection/redis_pool.py`（新增）
  - `src/connection/pool_creator.py`（修改 - 注册 RedisPoolCreator）
  - `src/config/dbconfig.py`（修改 - 支持 Redis 配置项）
  - `pyproject.toml`（修改 - 添加 redis 依赖）
  - `requirements.txt`（修改）

**描述**：

基于 `redis-py` 实现 `RedisConnectionPool`，继承 `ConnectionPool` 抽象基类。

**改造要点**：
1. `RedisConnectionPool(ConnectionPool)` 使用 `redis.ConnectionPool` 作为底层实现
2. 实现抽象方法：`get_connection()`、`return_connection()`、`connection()`、`get_stats()`、`close_all_connections()`
3. `RedisPoolCreator(DatabasePoolCreator)` 创建 Redis 连接池
4. 在 `DatabasePoolFactory._creators` 中注册 `"redis": RedisPoolCreator()`
5. `database_config.json` 支持 Redis 配置项：`host/port/password/db/type="redis"`

**验收标准**：
- [x] `RedisConnectionPool` 继承 `ConnectionPool` 并实现所有抽象方法
- [x] Redis 连接池可正常创建和销毁
- [x] `MultiDBPoolManager` 可管理 Redis 连接池
- [x] `get_stats()` 返回 Redis 连接池统计信息

---

### Task 2.2：KVStoreFactory 抽象与 RedisFactory 实现

- **状态**：`[x]` 已完成
- **依赖**：Task 1.2, Task 2.1
- **涉及文件**：
  - `src/datasource/kv/__init__.py`（新增）
  - `src/datasource/kv/base.py`（新增 - KVStoreFactory ABC）
  - `src/datasource/kv/redis/__init__.py`（新增）
  - `src/datasource/kv/redis/redis_factory.py`（新增）
  - `src/datasource/kv/redis/redis_db_version.py`（新增）
  - `src/datasource/kv/redis/redis_health.py`（新增 - 完整实现含 Task 2.5）
  - `src/datasource/kv/redis/redis_commands.py`（新增 - 命令执行）
  - `src/datasource/kv/redis/redis_key_info.py`（新增 - Key 信息查询）
  - `src/datasource/kv/redis/redis_scan.py`（新增 - Key 扫描）
  - `src/datasource/__init__.py`（修改 - 注册 RedisFactory）

**描述**：

定义 KV 范式的抽象接口（不同于关系型的 6 方法），实现 RedisFactory。

**改造要点**：
1. `KVStoreFactory(DataSourceFactory)` 定义 KV 范式抽象方法：
   - `create_command_executor()` - 执行 Redis 命令
   - `create_key_info()` - Key 类型、大小、TTL 查询
   - `create_key_scanner()` - Key 模式扫描
   - `create_db_version()` - 版本查询（通用，继承自 DataSourceFactory）
   - `create_db_health()` - 健康检查（通用，继承自 DataSourceFactory）
2. `RedisFactory(KVStoreFactory)`，`paradigm = Paradigm.KV_STORE`，`name = "redis"`
3. `redis_db_version.py`：通过 `INFO` 获取 Redis 版本
4. `redis_health.py`：通过 `INFO`、`SLOWLOG`、`CLIENT LIST`、`MEMORY STATS` 实现健康检查
5. `redis_commands.py`：执行 Redis 命令（GET/SET/HGET/LPUSH/...），带权限校验
6. `redis_key_info.py`：查询 Key 的 TYPE、MEMORY USAGE、TTL
7. `redis_scan.py`：通过 SCAN 按 pattern 扫描 Key

**验收标准**：
- [x] `KVStoreFactory` 定义 KV 范式抽象接口
- [x] `RedisFactory` 注册到 `FactoryRegistry`
- [x] `get_factory_by_pool_name("redis_pool")` 返回 `RedisFactory`
- [x] 版本查询、健康检查功能可用
- [x] Key 信息查询、扫描功能可用

---

### Task 2.3：KV 范式工具集实现

- **状态**：`[x]` 已完成
- **依赖**：Task 1.3, Task 2.2
- **涉及文件**：
  - `src/tools/redis_command.py`（新增 - execute_command 工具）
  - `src/tools/get_key_info.py`（新增 - Key 信息查询工具）
  - `src/tools/scan_keys.py`（新增 - Key 扫描工具）
  - `src/tools/get_db_health.py`（修改 - 适配多范式，Redis 专用 prompt）
  - `src/tools/get_db_version.py`（修改 - 使用 FactoryRegistry 替代 DatabaseOperationFactory）
  - `src/tools/__init__.py`（无需修改，自动发现）

**描述**：

为 KV 范式实现 MCP 工具，工具自动被 `tools/__init__.py` 发现注册。

**改造要点**：
1. `RedisCommandTool(ToolsBase)`：
   - `name = "execute_command"`
   - `applicable_paradigms = [Paradigm.KV_STORE]`
   - 接收 `command`（如 GET/SET/HGET）和 `args` 参数
   - 通过 `KVStoreFactory.create_command_executor()` 执行
2. `GetKeyInfoTool(ToolsBase)`：
   - `name = "get_key_info"`
   - `applicable_paradigms = [Paradigm.KV_STORE]`
   - 接收 `key` 和 `pool_name`，返回 type/size/ttl
3. `ScanKeysTool(ToolsBase)`：
   - `name = "scan_keys"`
   - `applicable_paradigms = [Paradigm.KV_STORE]`
   - 接收 `pattern`（如 `user:*`）和 `pool_name`，返回匹配的 Key 列表
4. 通用工具 `get_db_health` 和 `get_db_version` 适配 KV 范式（通过工厂多态调用）

**验收标准**：
- [x] 3 个 KV 工具自动注册到 `ToolRegistry`
- [x] `list_tools()` 在有 Redis pool 时返回 KV 工具
- [x] `list_tools()` 在无 Redis pool 时不返回 KV 工具
- [x] `execute_command` 可执行 GET/SET 等命令
- [x] `get_key_info` 返回 Key 的类型、大小、TTL
- [x] `scan_keys` 按 pattern 返回匹配的 Key

---

### Task 2.4：Redis 权限模型实现

- **状态**：`[x]` 已完成
- **依赖**：Task 1.4, Task 2.2
- **涉及文件**：
  - `src/permission/redis_permission.py`（新增 - RedisPermissionPolicy + RedisCommandCategory）
  - `src/datasource/kv/redis/redis_factory.py`（修改 - 实现 create_permission_policy）
  - `src/datasource/kv/redis/redis_commands.py`（集成权限校验）

**描述**：

为 Redis 实现权限策略，映射 readonly/writer/admin 三档角色到 Redis 命令分类。

**改造要点**：
1. 定义 `RedisCommandCategory` 枚举：`READ`、`WRITE`、`ADMIN`、`DANGEROUS`
2. 命令到分类的映射表：
   - `readonly`: GET, HGET, LLEN, SCARD, EXISTS, TTL, TYPE, SCAN, INFO, ...
   - `writer`: APPEND, SET, HSET, LPUSH, RPUSH, SADD, ZADD, DEL, EXPIRE, ...
   - `admin`: CONFIG, FLUSHDB, FLUSHALL, SHUTDOWN, BGSAVE, DEBUG, ...
3. `RedisPermissionPolicy(PermissionPolicy)` 实现权限校验
4. `RedisFactory.create_permission_policy()` 返回 `RedisPermissionPolicy`

**验收标准**：
- [x] `RedisPermissionPolicy` 定义命令分类映射
- [x] readonly 角色只能执行读命令
- [x] writer 角色可执行读写命令但不能执行管理命令
- [x] admin 角色可执行所有命令
- [x] 危险命令（FLUSHALL/SHUTDOWN）仅 admin 可执行

---

### Task 2.5：Redis 健康检查实现

- **状态**：`[x]` 已完成
- **依赖**：Task 2.2
- **涉及文件**：
  - `src/datasource/kv/redis/redis_health.py`（完整实现 - 6 种 health_type）

**描述**：

实现 Redis 健康检查的完整诊断能力，覆盖连接、内存、慢查询、大 Key 等维度。

**改造要点**：
1. `health_type` 支持的类型：
   - `all`：全部检查
   - `connection`：连接数、客户端列表、拒绝连接
   - `memory`：内存使用、碎片率、淘汰策略、大 Key
   - `slowlog`：慢查询日志
   - `replication`：主从复制状态
   - `persistence`：RDB/AOF 持久化状态
2. 通过 `INFO` 各 section 获取数据
3. 通过 `SLOWLOG GET` 获取慢查询
4. 通过 `CLIENT LIST` 获取连接详情
5. 输出格式与关系型健康检查一致，供 `get_db_health` 工具的 prompt 使用

**验收标准**：
- [x] 6 种 health_type 均有实现（all/connection/memory/slowlog/replication/persistence）
- [x] `all` 汇总所有维度的诊断数据
- [x] 输出格式可被 `get_db_health` 工具的 prompt 模板使用
- [x] Redis 未配置某些功能（如 AOF）时给出友好提示

---

### Task 2.6：Redis 集成验证与文档

- **状态**：`[x]` 已完成（代码层面验证）
- **依赖**：Task 2.1 ~ Task 2.5 全部完成
- **涉及文件**：
  - `src/config/database_config.example.json`（修改 - 添加 Redis 配置示例）
  - `src/datasource/base.py`（修改 - 添加 create_permission_policy 方法）
  - `src/tools/get_db_version.py`（修改 - 异常处理兼容多范式）
  - `README.md`（修改 - 添加 Redis 使用说明）
  - `README-zh.md`（修改 - 添加 Redis 使用说明）

**验收标准**：
- [x] Redis 连接池初始化正常（RedisPoolCreator 注册到 DatabasePoolFactory）
- [x] KV 工具在 MCP 客户端中可见且可用（applicable_paradigms = [KV_STORE]）
- [x] 关系型工具在仅有 Redis pool 时不可见（list_tools 按 paradigm 过滤）
- [x] 混合 pool（MySQL + Redis）时两种范式的工具均可见（_get_registered_paradigms 收集所有范式）
- [x] Redis 健康检查输出完整诊断报告（6 种 health_type）
- [x] Redis 权限校验生效（RedisPermissionPolicy 在 execute_command 中调用）
- [x] 文档更新完成（README.md + README-zh.md + database_config.example.json）

---

## Phase 3：MongoDB 集成

> 验证文档范式抽象。

### Task 3.1：MongoDB 连接池实现

- **状态**：`[x]` 已完成
- **依赖**：Phase 1 完成, Phase 2 验证抽象层通用性
- **涉及文件**：
  - `src/connection/mongodb_pool.py`（新增）
  - `src/connection/pool_creator.py`（修改）
  - `pyproject.toml`（修改 - 添加 motor 依赖）

**验收标准**：
- [x] `MongoDBConnectionPool` 继承 `ConnectionPool`
- [x] MongoDB 连接池可正常创建和销毁
- [x] `get_stats()` 返回连接池统计信息

---

### Task 3.2：DocumentFactory 抽象与 MongoDBFactory 实现

- **状态**：`[x]` 已完成
- **依赖**：Task 3.1
- **涉及文件**：
  - `src/datasource/document/__init__.py`（新增）
  - `src/datasource/document/base.py`（新增 - DocumentFactory ABC）
  - `src/datasource/document/mongodb/__init__.py`（新增）
  - `src/datasource/document/mongodb/mongodb_factory.py`（新增）
  - `src/datasource/document/mongodb/mongodb_db_version.py`（新增）
  - `src/datasource/document/mongodb/mongodb_health.py`（新增）
  - `src/datasource/document/mongodb/mongodb_queries.py`（新增 - 查询执行）
  - `src/datasource/document/mongodb/mongodb_schema.py`（新增 - Schema 推断）
  - `src/datasource/document/mongodb/mongodb_collections.py`（新增 - 集合列表）
  - `src/datasource/document/mongodb/mongodb_indexes.py`（新增 - 索引信息）
  - `src/datasource/document/mongodb/mongodb_explain.py`（新增 - 执行计划）

**验收标准**：
- [x] `DocumentFactory` 定义文档范式抽象接口
- [x] `MongoDBFactory` 注册到 `FactoryRegistry`
- [x] 版本查询、健康检查、集合列表、Schema 推断、索引查询、执行计划功能可用

---

### Task 3.3：文档范式工具集实现

- **状态**：`[x]` 已完成
- **依赖**：Task 3.2
- **涉及文件**：
  - `src/tools/mongo_query.py`（新增 - execute_mongo_query 工具）
  - `src/tools/get_collection_schema.py`（新增）
  - `src/tools/get_collection_names.py`（新增）
  - `src/tools/get_collection_indexes.py`（新增）
  - `src/tools/mongo_explain.py`（新增 - 执行计划分析）

**验收标准**：
- [x] 5 个文档范式工具自动注册
- [x] 工具按范式动态暴露
- [x] 查询执行、Schema 推断、集合列表、索引信息、执行计划功能正常

---

### Task 3.4：MongoDB 权限模型与健康检查

- **状态**：`[x]` 已完成
- **依赖**：Task 3.2, Task 3.3
- **涉及文件**：
  - `src/permission/mongo_permission.py`（新增）
  - `src/datasource/document/mongodb/mongodb_health.py`（完善）

**验收标准**：
- [x] `MongoPermissionPolicy` 映射 readonly/writer/admin 到 MongoDB 操作
- [x] 健康检查覆盖：连接数、内存、慢查询、副本集状态、索引统计
- [x] 权限校验生效

---

### Task 3.5：MongoDB 集成验证与文档

- **状态**：`[x]` 已完成
- **依赖**：Task 3.1 ~ Task 3.4
- **涉及文件**：
  - `src/config/database_config.example.json`（修改）
  - `README.md`（修改）
  - `README-zh.md`（修改）

**验收标准**：
- [x] MongoDB 连接池初始化正常
- [x] 文档范式工具可用
- [x] 混合 pool（MySQL + Redis + MongoDB）时三种范式的工具均可见
- [x] 文档更新完成

---

## Phase 4：向量数据库集成

> 切入 AI/LLM 生态，支持 RAG 场景。

### Task 4.1：向量数据库连接池实现

- **状态**：`[ ]` 未开始
- **依赖**：Phase 1 完成
- **涉及文件**：
  - `src/connection/milvus_pool.py`（新增）
  - `src/connection/pool_creator.py`（修改）
  - `pyproject.toml`（修改 - 添加 pymilvus 依赖）

**验收标准**：
- [ ] `MilvusConnectionPool` 继承 `ConnectionPool`
- [ ] Milvus 连接池可正常创建和销毁

---

### Task 4.2：VectorFactory 抽象与 MilvusFactory 实现

- **状态**：`[ ]` 未开始
- **依赖**：Task 4.1
- **涉及文件**：
  - `src/datasource/vector/__init__.py`（新增）
  - `src/datasource/vector/base.py`（新增 - VectorFactory ABC）
  - `src/datasource/vector/milvus/__init__.py`（新增）
  - `src/datasource/vector/milvus/milvus_factory.py`（新增）
  - `src/datasource/vector/milvus/milvus_db_version.py`（新增）
  - `src/datasource/vector/milvus/milvus_health.py`（新增）
  - `src/datasource/vector/milvus/milvus_search.py`（新增 - 向量搜索）
  - `src/datasource/vector/milvus/milvus_collection_info.py`（新增 - 集合信息）
  - `src/datasource/vector/milvus/milvus_index_info.py`（新增 - 索引信息）

**验收标准**：
- [ ] `VectorFactory` 定义向量范式抽象接口
- [ ] `MilvusFactory` 注册到 `FactoryRegistry`
- [ ] 向量搜索、集合信息、索引信息功能可用

---

### Task 4.3：向量范式工具集实现

- **状态**：`[ ]` 未开始
- **依赖**：Task 4.2
- **涉及文件**：
  - `src/tools/vector_search.py`（新增 - execute_vector_search 工具）
  - `src/tools/get_collection_info.py`（新增 - 向量集合信息）
  - `src/tools/get_vector_index_info.py`（新增 - 向量索引信息）

**验收标准**：
- [ ] 3 个向量范式工具自动注册
- [ ] 向量搜索工具支持相似度查询
- [ ] 集合信息工具返回维度、距离度量等
- [ ] 索引信息工具返回索引类型（HNSW/IVF）、参数

---

### Task 4.4：Milvus 权限模型与健康检查

- **状态**：`[ ]` 未开始
- **依赖**：Task 4.2
- **涉及文件**：
  - `src/permission/milvus_permission.py`（新增）
  - `src/datasource/vector/milvus/milvus_health.py`（完善）

**验收标准**：
- [ ] `MilvusPermissionPolicy` 映射角色到 Milvus 操作
- [ ] 健康检查覆盖：节点状态、索引构建进度、查询延迟、内存使用

---

### Task 4.5：向量数据库集成验证与文档

- **状态**：`[ ]` 未开始
- **依赖**：Task 4.1 ~ Task 4.4
- **涉及文件**：
  - `src/config/database_config.example.json`（修改）
  - `README.md`（修改）
  - `README-zh.md`（修改）

**验收标准**：
- [ ] Milvus 连接池初始化正常
- [ ] 向量范式工具可用
- [ ] 混合 pool 场景下工具按范式正确暴露
- [ ] 文档更新完成

---

## Phase 5：Elasticsearch + Kafka 集成

> 覆盖搜索与消息队列场景，完成多范式验证。

### Task 5.1：Elasticsearch 连接池与工厂

- **状态**：`[ ]` 未开始
- **依赖**：Phase 1 完成
- **涉及文件**：
  - `src/connection/elasticsearch_pool.py`（新增）
  - `src/datasource/search_engine/__init__.py`（新增）
  - `src/datasource/search_engine/base.py`（新增 - SearchEngineFactory ABC）
  - `src/datasource/search_engine/elasticsearch/__init__.py`（新增）
  - `src/datasource/search_engine/elasticsearch/es_factory.py`（新增）
  - `src/datasource/search_engine/elasticsearch/es_db_version.py`（新增）
  - `src/datasource/search_engine/elasticsearch/es_health.py`（新增）
  - `src/datasource/search_engine/elasticsearch/es_query.py`（新增 - DSL 查询）
  - `src/datasource/search_engine/elasticsearch/es_mapping.py`（新增 - 索引 mapping）
  - `src/datasource/search_engine/elasticsearch/es_indices.py`（新增 - 索引列表）
  - `pyproject.toml`（修改 - 添加 elasticsearch 依赖）

**验收标准**：
- [ ] `SearchEngineFactory` 定义搜索引擎范式抽象接口
- [ ] `ElasticsearchFactory` 注册到 `FactoryRegistry`
- [ ] DSL 查询、mapping 查询、索引列表功能可用

---

### Task 5.2：搜索引擎范式工具集与权限

- **状态**：`[ ]` 未开始
- **依赖**：Task 5.1
- **涉及文件**：
  - `src/tools/es_query.py`（新增 - execute_es_query 工具）
  - `src/tools/get_index_mapping.py`（新增）
  - `src/tools/get_index_names.py`（新增）
  - `src/permission/es_permission.py`（新增）

**验收标准**：
- [ ] 3 个搜索引擎工具自动注册
- [ ] ES 健康检查覆盖：集群健康、分片状态、线程池、段合并
- [ ] 权限模型映射 readonly/writer/admin 到 ES 操作

---

### Task 5.3：Kafka 连接池与工厂

- **状态**：`[ ]` 未开始
- **依赖**：Phase 1 完成
- **涉及文件**：
  - `src/connection/kafka_pool.py`（新增）
  - `src/datasource/message_queue/__init__.py`（新增）
  - `src/datasource/message_queue/base.py`（新增 - MessageQueueFactory ABC）
  - `src/datasource/message_queue/kafka/__init__.py`（新增）
  - `src/datasource/message_queue/kafka/kafka_factory.py`（新增）
  - `src/datasource/message_queue/kafka/kafka_health.py`（新增）
  - `src/datasource/message_queue/kafka/kafka_topics.py`（新增 - Topic 管理）
  - `src/datasource/message_queue/kafka/kafka_consumer_groups.py`（新增 - 消费者组管理）
  - `pyproject.toml`（修改 - 添加 kafka-python 依赖）

**验收标准**：
- [ ] `MessageQueueFactory` 定义消息队列范式抽象接口
- [ ] `KafkaFactory` 注册到 `FactoryRegistry`
- [ ] Topic 列表、消费者组、延迟（Lag）查询功能可用

---

### Task 5.4：消息队列范式工具集与权限

- **状态**：`[ ]` 未开始
- **依赖**：Task 5.3
- **涉及文件**：
  - `src/tools/list_topics.py`（新增）
  - `src/tools/get_topic_info.py`（新增）
  - `src/tools/get_consumer_lag.py`（新增）
  - `src/permission/kafka_permission.py`（新增）

**验收标准**：
- [ ] 3 个消息队列工具自动注册
- [ ] Kafka 健康检查覆盖：Broker 状态、分区 Leader、ISR、消费者延迟
- [ ] 权限模型映射角色到 Kafka 操作

---

### Task 5.5：ES + Kafka 集成验证

- **状态**：`[ ]` 未开始
- **依赖**：Task 5.1 ~ Task 5.4
- **涉及文件**：无新增，验证现有

**验收标准**：
- [ ] ES 和 Kafka 连接池初始化正常
- [ ] 搜索引擎和消息队列范式工具可用
- [ ] 混合 pool 场景下工具按范式正确暴露
- [ ] 6 种范式的工具互不干扰

---

### Task 5.6：全量集成验证与文档更新

- **状态**：`[ ]` 未开始
- **依赖**：Task 5.5 + 所有前序 Phase 完成
- **涉及文件**：
  - `src/config/database_config.example.json`（修改 - 添加 ES + Kafka 配置示例）
  - `README.md`（修改 - 全面更新）
  - `README-zh.md`（修改 - 全面更新）
  - `CLAUDE.md`（修改 - 更新架构说明）
  - `Dockerfile`（修改 - 如需新增系统依赖）
  - `docker-compose.yml`（修改 - 如需新增服务）

**验收标准**：
- [ ] 6 种范式（关系型/KV/文档/向量/搜索/消息队列）全部可用
- [ ] 混合 pool 场景下所有范式工具正确暴露
- [ ] 权限校验按范式和 pool 正确生效
- [ ] 文档全面更新
- [ ] Docker 部署正常
- [ ] CLAUDE.md 架构说明已更新

---

## 五、风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 抽象层设计过度，导致现有关系型功能回归 | 高 | Phase 1 完成后做完整回归验证（Task 1.8） |
| 新增依赖导致包体积膨胀 | 中 | 按需安装：核心包 + 可选数据源扩展包 |
| 不同 Python 版本下驱动兼容性 | 中 | pyproject.toml 锁定最低版本，CI 测试多版本 |
| MCP 工具数量膨胀，客户端上下文溢出 | 中 | 工具按范式动态暴露，非全量返回 |
| 重构周期长，中间状态不稳定 | 高 | 每个 Task 独立可提交，保持主分支随时可用 |

## 六、依赖关系图

```
Phase 0 (安全修复)
  ├── Task 0.1 ──────────────────────┐
  ├── Task 0.2 ──────┐               │
  └── Task 0.3       │               │
                    │               │
Phase 1 (抽象层拆分) │               │
  ├── Task 1.1       │               │
  ├── Task 1.2 ──┐   │               │
  ├── Task 1.3   │   │               │
  ├── Task 1.4 ←─┼───┘               │
  ├── Task 1.5   │                   │
  ├── Task 1.6 ←─┘                   │
  ├── Task 1.7 ←─────────────────────┘
  └── Task 1.8 (验证)
        │
        ├──→ Phase 2 (Redis)
        │      Task 2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 2.6
        │
        ├──→ Phase 3 (MongoDB)
        │      Task 3.1 → 3.2 → 3.3 → 3.4 → 3.5
        │
        ├──→ Phase 4 (向量数据库)
        │      Task 4.1 → 4.2 → 4.3 → 4.4 → 4.5
        │
        └──→ Phase 5 (ES + Kafka)
               Task 5.1 → 5.2 → 5.3 → 5.4 → 5.5 → 5.6
```

> Phase 2~5 之间相互独立，可根据优先级调整执行顺序。但每个 Phase 内部任务必须按序执行。
