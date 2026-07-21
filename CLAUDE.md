# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SmartDB 是一个通用数据库网关，实现 MCP (Model Context Protocol) 服务器接口，允许 MCP 客户端连接并操作多种数据库。除基础连接探索外，还提供 OAuth 2.0 认证、健康检查、SQL 优化、索引健康检测等高级功能。

支持数据库：MySQL、PostgreSQL、Oracle、SQL Server、达梦 (DM8)、Redis (KV)、MongoDB (文档)。

## Common Commands

### 依赖安装
```bash
uv sync
```

### 本地启动 (默认 streamable_http 模式，监听 0.0.0.0:3000)
```bash
uv run -m core.server
uv run -m core.server --mode sse
uv run -m core.server --mode stdio
uv run -m core.server --envfile /path/to/.env
uv run -m core.server --oauth=true   # 仅 streamable_http 模式支持
```

### Docker
```bash
docker-compose up -d
docker-compose logs -f smartdb
docker build -t smartdb-mcp:latest .
```

### pip 包入口
安装后通过 `smartdb` 命令启动（见 `pyproject.toml` 中的 `[project.scripts]`）。

### 测试
仓库当前未配置测试框架或测试用例。新增功能时如需测试，请先与用户确认测试方案。

## Architecture

### 整体分层

```
src/core/server.py        — MCP 服务器入口（stdio / sse / streamable_http 三种模式）
src/tools/                — MCP 工具层（每个工具对外暴露给 MCP 客户端）
src/databases/            — 数据库操作抽象工厂层（按数据库类型分目录）
src/connection/           — 连接池管理（SQLAlchemy QueuePool，多库单例）
src/config/               — 配置加载（database_config.json + .env）
src/oauth/                — OAuth 2.0 认证（JWT + 密码模式 + refresh_token）
src/utils/                — SQL 执行与权限校验工具
src/static/login/         — Vue 构建产物（OAuth 登录页，勿手改）
```

### 启动流程 (core/server.py:main)

1. `load_dotenv` 加载 `.env`（默认 `src/config/.env`，可由 `--envfile` 覆盖）
2. `MultiDBPoolManager.init_from_config()` 初始化所有连接池（单例，整个进程共享）
3. 根据 `--mode` 选择 `run_stdio` / `run_sse` / `run_streamable_http`
4. streamable_http 模式下，若 `--oauth=true`，挂载 `OAuthMiddleware`、`/login`、`/mcp/authorize` 路由及静态文件

### 关键设计模式

**1. 工具自动注册（src/tools/base.py + src/tools/__init__.py）**
- `ToolsBase` 子类在 `__init_subclass__` 中自动调用 `ToolRegistry.register(cls)`，无需手动注册
- `tools/__init__.py` 动态扫描目录下所有 `.py` 模块并导入以触发注册；**新增工具文件放入 `src/tools/` 即可被自动发现**，类名需以 `Tool` 结尾
- `server.py` 通过 `ToolRegistry.get_all_tools()` 向 MCP 客户端暴露工具列表

**2. 数据库操作抽象工厂（src/databases/）**
- `DatabaseOperationFactory` 为抽象工厂，定义 6 个 create 方法：`db_version / table_description / table_name / table_index / db_health / sql_optimize`
- 每种数据库一个 `XxxFactory`（mysql/postgresql/oracle/mssqlserver/dameng），工厂 `name` 属性对应 `database_config.json` 中的 `type` 字段
- **工厂延迟注册**：`__init_subclass__` 将子类放入 `_pending_factories`，由 `databases/__init__.py` 调用 `register_all_factories()` 统一注册，避免循环导入
- 通过 `FactoryRegistry.get_factory_by_pool_name(pool_name)` 根据 pool 配置的 `type` 取得对应工厂实例

**3. 连接池单例（src/connection/pool_manager.py）**
- `MultiDBPoolManager` 是线程安全单例，`get_instance()` 双重检查锁
- 启动时一次性加载所有 pool，运行时通过 `MultiDBPoolManager.get_pool(name)` 获取
- `pool_creator.py` 中 `DatabasePoolFactory._creators` 字典硬编码 5 种 `DatabasePoolCreator`，**新增数据库类型需在此注册**

**4. SQL 权限校验（src/utils/execute_sql_util.py + src/config/dbconfig.py）**
- `ROLE_PERMISSIONS` 定义三档角色：`readonly` / `writer` / `admin`
- 所有 SQL 执行前由 `ExecuteSqlUtil.extract_operations` 提取操作类型，`check_permissions` 校验
- `execute_single_statement` 是所有数据库操作的统一入口；非查询语句失败会 rollback

### 配置文件

**`src/config/database_config.json`** — 数据库连接配置
- `default` key 为必需项，其他按需添加
- 通用字段：`host/port/user/password/database/role/pool_size/max_overflow/pool_recycle/pool_timeout/type`
- 特殊字段：`schema`（PG/SQL Server）、`service_name`（Oracle）、`db`（Redis）、`auth_source`/`min_pool_size`（MongoDB）
- `type` 取值：`mysql` / `postgresql` / `oracle` / `mssqlserver` / `dameng` / `redis` / `mongodb`
- 配置文件路径由环境变量 `DATABASE_CONFIG_FILE` 指定，默认 `src/config/database_config.json`

**`src/config/.env`** — OAuth 与环境配置
- `CLIENT_ID` / `CLIENT_SECRET`：OAuth 客户端凭据
- `TOKEN_SECRET_KEY`：JWT 签名密钥
- `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS`：令牌有效期
- `OAUTH_USER_NAME` / `OAUTH_USER_PASSWORD`：登录账号密码
- **注意**：修改 `CLIENT_ID` / `CLIENT_SECRET` 时需同步修改 `src/static/login/config.js`

### 工具列表（src/tools/）

| 工具 | 用途 |
|------|------|
| `execute_sql` | 执行 `sql_creator` 生成的 SQL；支持分号分隔多语句 |
| `sql_creator` | **生成 SQL 的唯一推荐入口**；基于真实元数据生成，禁止模型自行编写 SQL |
| `sql_optimize` | SQL 性能优化；需传入 SQL 及涉及的表（`数据库.模式.表名` 格式，逗号分隔） |
| `get_db_health` | 数据库健康诊断；`health_type`: all/index/connection/blocking/resources |
| `get_table_name` | 按关键词搜索表名；`SEARCH_ALL_TABLES` 查询所有表 |
| `get_table_desc` | 查询表结构（字段、注释），支持多表逗号分隔 |
| `get_table_index` | 查询表索引信息 |
| `get_db_version` | 查询数据库版本 |
| `execute_command` | 执行 Redis 命令（KV 范式） |
| `get_key_info` | 查询 Redis Key 详情（KV 范式） |
| `scan_keys` | 按 pattern 扫描 Redis Key（KV 范式） |
| `execute_mongo_query` | 执行 MongoDB 查询 find/aggregate（文档范式） |
| `get_collection_schema` | 推断 MongoDB 集合 Schema（文档范式） |
| `get_collection_names` | 查询 MongoDB 集合列表（文档范式） |
| `get_collection_indexes` | 查询 MongoDB 集合索引（文档范式） |
| `mongo_explain` | MongoDB 查询执行计划分析（文档范式） |

### OAuth 2.0 流程

- 密码模式：`POST /mcp/authorize`，grant_type=password
- 前端密码采用 SHA256 双重哈希（密码+salt → +timestamp），服务端用相同算法校验
- 时间戳有效期 5 分钟，通过 `X-Timestamp` / `X-Salt` 请求头传递
- `OAuthMiddleware` 默认排除 `/login` 和 `/mcp/authorize`，其他路径需 `Authorization: Bearer <token>`
- token 类型区分 `access_token` / `refresh_token`

## Development Notes

### 新增 MCP 工具
1. 在 `src/tools/` 下新建 `.py` 文件，类名以 `Tool` 结尾并继承 `ToolsBase`
2. 设置 `name` 和 `description` 类属性
3. 实现 `get_tool_description()`（返回 `mcp.types.Tool`）和 `async run_tool(arguments)`
4. 无需修改其他文件，`tools/__init__.py` 会自动发现并注册

### 新增数据库类型支持

**关系型数据库**：
1. 在 `src/databases/<db_type>/` 下创建工厂类与 6 个操作实现类（参照 `mysql/` 目录结构）
2. 工厂类继承 `DatabaseOperationFactory`，设置 `name` 属性
3. 在 `src/databases/__init__.py` 中导入新工厂
4. 在 `src/connection/pool_creator.py` 的 `DatabasePoolFactory._creators` 中注册对应的 `PoolCreator`
5. 在 `src/databases/base/base.py` 中已定义的抽象接口需全部实现

**非关系型数据源（KV/文档/向量等）**：
1. 在 `src/datasource/<paradigm>/<db_type>/` 下创建工厂类与操作实现类
2. 工厂类继承对应范式基类（`KVStoreFactory` / `DocumentFactory` / ...），设置 `name` 属性
3. 在 `src/datasource/__init__.py` 中添加 `_register_<db_type>_factory()` 函数并调用
4. 在 `src/connection/pool_creator.py` 中注册对应的 `PoolCreator`
5. 在 `src/permission/` 下创建对应的权限策略类
6. 在 `src/tools/` 下创建范式专属工具（类名以 `Tool` 结尾，设置 `applicable_paradigms`）

### 代码规范
- 代码注释、命名、类型定义保持英文
- 对话与文档使用中文（继承自上层 `python/CLAUDE.md`）
- Python ≥ 3.11，使用 `uv` 作为包管理器
- 模块导入使用绝对路径（如 `from config.dbconfig import ...`），依赖 `PYTHONPATH=src`（Docker 中已配置）

### 打包说明
`pyproject.toml` 使用 hatchling 作为构建后端，wheel 包含 `src/core`、`src/config`、`src/connection`、`src/tools`、`src/oauth`、`src/utils`、`src/databases`、`src/datasource`、`src/permission`、`src/static` 及 `src/datasource/` 下的范式子目录。修改这些目录结构时需同步更新 `[tool.hatch.build.targets.wheel]` 配置。

## 重构项目：多范式数据源集成

项目正在进行抽象层重构，目标是从单一关系型数据库网关升级为多范式数据基础设施网关（关系型/KV/文档/向量/搜索/消息队列）。完整方案见 `docs/REFACTORING_PLAN.md`。

### 重构准则（必须严格遵守）

1. **按步骤执行**：必须按 `docs/REFACTORING_PLAN.md` 中的 Phase 和 Task 顺序执行，不得跳步。每个 Phase 内部任务有依赖关系，必须按序完成；Phase 2~5 之间相互独立，可根据优先级调整顺序。

2. **进度同步**：每完成一个 Task，必须立即更新 `docs/REFACTORING_PLAN.md` 中对应任务的状态和进度表：
   - 任务状态：`[ ]` 未开始 → `[~]` 进行中 → `[x]` 已完成
   - 进度总览表中的"已完成"计数和"状态"列同步更新
   - "最后更新"日期同步更新
   - 验收标准 checkbox 逐项勾选

3. **单步提交**：每个 Task 完成后应作为一个独立的 git commit，commit message 格式：`refactor(phaseX-taskY): 简述`。安全修复类任务使用 `fix(phase0-taskY): 简述`。

4. **验收驱动**：每个 Task 有明确的验收标准，必须全部满足才能标记为 `[x]` 已完成。未满足的验收标准保持 `[ ]` 未勾选状态。

5. **不破坏现有功能**：重构期间现有 5 种关系型数据库（MySQL/PostgreSQL/Oracle/SQL Server/达梦）的功能必须保持可用。任何破坏性变更需在 Task 描述中明确标注，并在 Task 1.8 集成验证中确认。

6. **开始前先读方案**：每次开始一个新的 Task 前，必须先读取 `docs/REFACTORING_PLAN.md` 中该 Task 的完整描述、依赖、涉及文件和验收标准，确保理解任务范围。
