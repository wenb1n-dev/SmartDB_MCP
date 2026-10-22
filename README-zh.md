[![简体中文](https://img.shields.io/badge/简体中文-点击查看-orange)](README-zh.md)
[![English](https://img.shields.io/badge/English-Click-yellow)](README.md)

<img width="1023" height="270" alt="image" src="https://github.com/user-attachments/assets/4b282174-dd45-4edb-9de8-9b14e2c59a9e" />

# SmartDB
## 好用就帮忙点个赞，支持一下呀，拜托各位精英们～。
SmartDB 是一个通用多范式数据基础设施网关，实现了模型上下文协议（Model Context Protocol，简称 MCP）服务器接口，允许与 MCP 兼容的客户端以统一方式连接并探索不同的数据源。

目前覆盖 **6 种数据范式、10 种数据源**：5 种关系型数据库（MySQL、PostgreSQL、Oracle、SQL Server、达梦）、KV 存储（Redis）、文档型（MongoDB）、向量型（Milvus）、搜索引擎（Elasticsearch）、消息队列（Apache Kafka），共提供 26 个 MCP 工具，并按连接池所属范式动态过滤暴露。

与同类产品相比，SmartDB不仅提供基本的数据库连接和探索功能，还增加了OAuth2.0认证、健康检查、SQL优化和索引健康检测等高级功能，使数据库管理和维护更加安全、智能化。

<img width="1303" height="697" alt="image" src="https://github.com/user-attachments/assets/9340f85e-28b0-45f2-8cb2-768b0d1c8b5c" />


# 目前支持的数据库
| 数据库 | 类型 | 支持 | 描述                          |
|-----|------|----|-----------------------------|
| MySQL | 关系型 | √  | Mysql 5.6+、Mariadb 10+ 均支持  |
| PostgreSQL | 关系型 | √  | PostgreSQL 9.6+、YMatrix 均支持 |
| Oracle | 关系型 | √  | Oracle 12 +                 |
| SQL Server | 关系型 | √  | Microsoft SQL Server 2012 + |
| 达梦数据库 | 关系型 | √  | DM8                         |
| Redis | KV 存储 | √  | Redis 5.0+                  |
| MongoDB | 文档型 | √  | MongoDB 4.0+                |
| Milvus | 向量型 | √  | Milvus 2.3+                 |
| Elasticsearch | 搜索引擎 | √  | Python 驱动 ≥ 8.0，自动适配 ES 7/8/9 服务端 |
| Apache Kafka | 消息队列 | √  | kafka-python-ng 驱动 ≥ 2.2.2 |

# 工具列表

工具总数共 26 个。其中 `get_db_health`、`get_db_version` 为全范式通用工具，其余工具按连接池所属范式暴露。

## 关系型数据库工具
| 工具名称            | 描述                                                                                                                                 |
|-----------------|------------------------------------------------------------------------------------------------------------------------------------|
| execute_sql     | sql执行工具，根据权限配置可执行["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "TRUNCATE"] 命令 |
| get_db_health   | 分析数据库的健康状态（连接情况、事务情况、运行情况、锁情况检测），输出专业的诊断报告及解决方案                                                                                    |
| get_table_desc  | 根据表名搜索数据库中对应的表结构,支持多表查询                                                                                                            |
| get_table_index | 根据表名搜索数据库中对应的表索引,支持多表查询                                                                                                            |
| get_table_name  | 数据库表名查询工具。用于查询数据库中的所有表名或将根据表的中文名称或表描述搜索数据库中对应的表名                                                                                   |
| get_db_version  | 数据库版本查询工具                                                                                                                          |
| sql_creator     | SQL查询生成工具，根据不同的数据库类型生成对应SQL查询语句
| sql_optimize    | 专业的SQL性能优化工具，基于执行计划、表结构信息、表数据量、表索引提供专家级优化建议                                                                                        |

## KV 存储工具（Redis）
| 工具名称            | 描述                                                                 |
|-----------------|--------------------------------------------------------------------|
| execute_command | 执行 Redis 命令（GET/SET/HGET/LPUSH 等），带权限校验                    |
| get_key_info    | 查询 Redis Key 的详细信息（类型、大小、TTL、内存使用）                   |
| scan_keys       | 按 pattern 扫描 Redis Key（使用 SCAN 命令，非阻塞）                    |
| get_db_health   | 分析 Redis 健康状态（连接、内存、慢查询、复制、持久化），输出诊断报告        |
| get_db_version  | 查询 Redis 版本号                                                    |

## 文档存储工具（MongoDB）
| 工具名称            | 描述                                                                 |
|-----------------|--------------------------------------------------------------------|
| execute_mongo_query | 执行 MongoDB 查询（find/aggregate），支持过滤、投影、排序、分页        |
| execute_mongo_write | 执行 MongoDB 写入（insert_one/insert_many/update_one/update_many/replace_one/delete_one/delete_many），带权限校验，支持扩展 JSON（$oid/$date）；update_many/delete_many 必须显式传入 filter |
| get_collection_schema | 通过采样文档推断集合 Schema（字段名、类型、出现频率）                   |
| get_collection_names | 查询数据库中的集合列表，支持按名称模式过滤                              |
| get_collection_indexes | 查询集合索引信息，支持查询单个或所有集合                               |
| mongo_explain | 分析 MongoDB 查询执行计划，包括查询计划、执行统计、索引使用情况          |
| get_db_health | 分析 MongoDB 健康状态（连接、内存、慢查询、复制、索引），输出诊断报告    |
| get_db_version | 查询 MongoDB 版本号                                                  |

## 向量存储工具（Milvus）
| 工具名称            | 描述                                                                 |
|-----------------|--------------------------------------------------------------------|
| execute_vector_search | 在向量集合中执行相似度搜索，返回最近的 K 个邻居                           |
| get_collection_info | 查询向量集合的元数据（维度、距离度量、Schema、实体数量等）                   |
| get_vector_index_info | 查询向量集合的索引信息（索引类型、参数、构建进度等）                        |
| get_db_health | 分析 Milvus 健康状态（连接、内存、索引、延迟、节点），输出诊断报告        |
| get_db_version | 查询 Milvus 版本号                                                  |

## 搜索引擎工具（Elasticsearch）
| 工具名称            | 描述                                                                 |
|-----------------|--------------------------------------------------------------------|
| execute_es_query | 执行 Elasticsearch DSL 查询（search/count/aggregate），支持完整 DSL |
| get_index_mapping | 查询索引 Mapping（字段类型、分析器）与设置                          |
| get_index_names | 查询 Elasticsearch 索引列表                                         |
| get_db_health | 分析 Elasticsearch 健康状态（集群状态、分片、节点），输出诊断报告    |
| get_db_version | 查询 Elasticsearch 版本号                                          |

## 消息队列工具（Apache Kafka）
| 工具名称            | 描述                                                                 |
|-----------------|--------------------------------------------------------------------|
| list_topics | 查询 Kafka Topic 列表                                               |
| get_topic_info | 查询 Topic 详情：分区、Leader、副本、offset                         |
| get_consumer_lag | 查询消费者组延迟 Lag                                                |
| get_db_health | 分析 Kafka 健康状态（Broker、Topic/分区、ISR、消费者组），输出诊断报告 |
| get_db_version | 查询 Kafka 集群版本与 Broker 元数据                                 |

# 使用方法
## env 配置文件说明
```aiignore
# 数据库配置文件路径
DATABASE_CONFIG_FILE=/Volumes/SmartDB/src/config/database_config.json

#========Server========
# 服务器监听地址
SERVER_HOST=0.0.0.0
# 服务器监听端口
SERVER_PORT=3000

#========OAuth2========
# OAuth2 客户端 ID
CLIENT_ID=smart_db_client_id
# OAuth2 客户端密钥
CLIENT_SECRET=smart_db_client_secret
# 访问令牌过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=30
# 刷新令牌过期时间（天）
REFRESH_TOKEN_EXPIRE_DAYS=30
# 令牌加密密钥
TOKEN_SECRET_KEY=smart_db_token_secret
# 用户名
OAUTH_USER_NAME=admin
# 密码
OAUTH_USER_PASSWORD=wenb1n
```

注意：若调整了oauth配置中客户端的id以及密钥，请同时修改前段代码中static/config文件中的对应配置


## 数据库连接配置说明
```json
{
  "default": {
    "host": "192.168.xxx.xxx",
    "port": 3306,
    "user": "root",
    "password": "root",
    "database": "a_llm",
    "role": "readonly",
    "pool_size": 10,
    "max_overflow": 20,
    "pool_recycle": 3600,
    "pool_timeout": 30,
    "type": "mysql"
  },
  "postgresql": {
    "host": "192.168.xxx.xxx",
    "port": 5432,
    "user": "postgres",
    "password": "123456",
    "database": "postgres",
    "schema": "public",
    "role": "readonly",
    "pool_size": 5,
    "max_overflow": 10,
    "pool_recycle": 3600,
    "pool_timeout": 30,
    "type": "postgresql"
  },
  "oracle": {
    "host": "192.168.xxx.xxx",
    "port": 1521,
    "user": "U_ORACLE",
    "password": "123456",
    "database": "123456",
    "service_name": "ORCL",
    "role": "readonly",
    "pool_size": 5,
    "max_overflow": 10,
    "pool_recycle": 3600,
    "pool_timeout": 30,
    "type": "oracle"
  },
  "mssql": {
    "host": "192.168.xxx.xxx",
    "port": 1433,
    "user": "test",
    "password": "123456",
    "database": "TEST",
    "schema": "dbo",
    "role": "readonly",
    "pool_size": 5,
    "max_overflow": 10,
    "pool_recycle": 3600,
    "pool_timeout": 30,
    "type": "mssqlserver"
  },
  "redis": {
    "host": "127.0.0.1",
    "port": 6379,
    "password": "your_redis_password",
    "db": 0,
    "role": "readonly",
    "pool_size": 50,
    "type": "redis"
  },
  "mongodb": {
    "host": "127.0.0.1",
    "port": 27017,
    "user": "your_user",
    "password": "your_password",
    "database": "your_database",
    "auth_source": "admin",
    "role": "readonly",
    "pool_size": 50,
    "min_pool_size": 5,
    "type": "mongodb"
  },
  "milvus": {
    "host": "127.0.0.1",
    "port": 19530,
    "user": "your_user",
    "password": "your_password",
    "database": "default",
    "role": "readonly",
    "pool_size": 10,
    "type": "milvus"
  },
  "elasticsearch": {
    "host": "127.0.0.1",
    "port": 9200,
    "user": "your_user",
    "password": "your_password",
    "use_ssl": false,
    "verify_certs": true,
    "role": "readonly",
    "pool_size": 10,
    "type": "elasticsearch"
  },
  "kafka": {
    "host": "127.0.0.1",
    "port": 9092,
    "user": "your_user",
    "password": "your_password",
    "role": "readonly",
    "pool_size": 10,
    "type": "kafka"
  }
}

```

> Elasticsearch 与 Kafka 的 `user`/`password` 为可选项：无认证的集群直接省略即可；Kafka 同时提供 user/password 时使用 SASL/PLAIN 认证。可直接参考 `src/config/database_config.example.json` 中的完整模板。
* 数据库连接参数说明

下表详细说明了数据库连接配置文件中各参数的含义和用法：

| 参数名 | 必需 | 类型 | 描述 |
|--------|------|------|------|
| host | 是 | string | 数据库服务器地址 |
| port | 是 | integer | 数据库服务器端口号 |
| user | 关系型、MongoDB、Milvus 必需；Elasticsearch、Kafka 无认证时可省略 | string | 数据库用户名 |
| password | 关系型、MongoDB、Milvus 必需；Elasticsearch、Kafka 无认证时可省略 | string | 数据库用户密码 |
| database | 关系型、MongoDB、Milvus 必需 | string | 要连接的数据库名称 |
| role | 是 | string | 用户角色，如 "readonly" 表示只读权限 |
| pool_size | 是 | integer | 连接池大小 |
| max_overflow | 关系型 | integer | 连接池最大溢出连接数 |
| pool_recycle | 关系型 | integer | 连接池回收时间（秒） |
| pool_timeout | 关系型 | integer | 连接池超时时间（秒） |
| type | 是 | string | 数据库类型，如 "mysql"、"postgresql"、"oracle"、"mssqlserver"、"dameng"、"redis"、"mongodb"、"milvus"、"elasticsearch"、"kafka" |

* 特定数据库额外参数

| 参数名 | 数据库类型 | 必需 | 类型 | 描述 |
|--------|------------|------|------|------|
| schema | PostgreSQL, SQL Server | 否 | string | 数据库模式 |
| service_name | Oracle | 否 | string | Oracle服务名 |
| db | Redis | 否 | integer | Redis 数据库索引，默认 0 |
| auth_source | MongoDB | 否 | string | 认证数据库，默认 "admin" |
| min_pool_size | MongoDB | 否 | integer | 最小连接池大小，默认 5 |
| token | Milvus | 否 | string | 认证令牌（替代 user/password） |
| use_ssl | Elasticsearch | 否 | boolean | 是否使用 HTTPS，默认 false |
| verify_certs | Elasticsearch | 否 | boolean | HTTPS 下是否校验证书，默认 true |

* role 权限控制配置项：只读（readonly）、读写（writer）、管理员（admin）。关系型数据库的角色与 SQL 操作分类对应关系如下：
```
    "readonly": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"],  # 只读权限
    "writer": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE"],  # 读写权限
    "admin": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE",
             "CREATE", "ALTER", "DROP", "TRUNCATE"]  # 管理员权限
```
非关系型数据源（Redis、MongoDB、Milvus、Elasticsearch、Kafka）同样使用 readonly/writer/admin 三档角色，底层按 READ / WRITE / ADMIN / DANGEROUS 四类操作做权限校验。例如 readonly 角色调用 `execute_mongo_write`、执行 Redis 写命令等会被拒绝。
   
* 注意

default 为默认数据库连接配置，必须配置，其他数据库配置请自行添加 

## pip安装和配置
1. 安装包
```bash
pip install SmartDB-MCP
```

参数说明：

- `--mode`：传输模式（`stdio`、`sse`、`streamablehttp`）
- `--envfile`：环境变量文件路径
- `--oauth`：启用 OAuth 认证（目前仅支持 `streamablehttp` 模式）

启动命令：
```bash
smartdb --envfile=/path/to/.env --oauth=true
```

## docker 启动
### 快速开始

#### 1. 构建并启动服务

```bash
# 修改自己的数据库连接配置文件路径
修改[docker-compose.yml] 中
    volumes:
      - 你的外部database_config.json地址:/app/config/database_config.json

# 使用docker-compose启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f smartdb
```

#### 2. 手动构建镜像

```bash
# 构建镜像
docker build -t smartdb-mcp:latest .

# 运行容器
docker run -d \
  --name smartdb-mcp-server \
  -p 3000:3000 \
  -e DATABASE_CONFIG_FILE=/app/src/config/database_config.json \
  -e CLIENT_ID=smart_db_client_id \
  -e CLIENT_SECRET=smart_db_client_secret \
  -e TOKEN_SECRET_KEY=your_secret_key \
  -v $(pwd)/src/config:/app/src/config:ro \
  -v $(pwd)/logs:/app/logs \
  smartdb-mcp:latest
```

## 代码启动

### 本地开发 Streamable Http 方式

- 使用 uv 启动服务

将以下内容添加到你的 mcp client 工具中，例如cursor、cline等

mcp json 如下
````
{
  "mcpServers": {
    "smartdb": {
      "name": "smartdb",
      "type": "streamableHttp",
      "description": "",
      "isActive": true,
      "url": "http://localhost:3000/mcp/"
    }
  }
}
````

启动命令
```
# 下载依赖
uv sync

# 启动
uv run -m core.server

# 自定义env文件位置
uv run -m core.server --envfile /path/to/.env
```

### 本地开发 SSE 方式

- 使用 uv 启动服务

将以下内容添加到你的 mcp client 工具中，例如cursor、cline等

mcp json 如下
````
{
  "mcpServers": {
    "smartdb": {
      "name": "smartdb",
      "description": "",
      "isActive": true,
      "url": "http://localhost:3000/sse"
    }
  }
}
````

启动命令
```
# 下载依赖
uv sync

# 启动
uv run -m core.server --mode sse

# 自定义env文件位置
uv run -m core.server --mode sse --envfile /path/to/.env
```

### 本地开发 STDIO 方式 

将以下内容添加到你的 mcp client 工具中，例如cursor、cline等

mcp json 如下
```
{
  "mcpServers": {
      "smartdb": {
          "name": "smartdb",
          "type": "stdio",
          "isActive": false,
          "registryUrl": "",
          "command": "uv",
          "args": [
            "--directory",
            "/Volumes/python/SmartDB/",
            "run",
            "-m",
            "core.server",
            "--mode",
            "stdio"
          ],
          "env": {
            "DATABASE_CONFIG_FILE": "/Volumes/database_config.json"
          }
      }
    }
  }
}  
```

## 支持OAuth 2.0 认证
1. 启动认证服务,默认使用自带的OAuth 2.0 密码模式认证，可以在env中修改自己的认证服务地址
```aiignore
uv run -m core.server --oauth=true
```

2. 访问 认证服务 http://localhost:3000/login ，默认帐号密码在 env 中配置
<img width="1777" height="950" alt="image" src="https://github.com/user-attachments/assets/20531bee-467f-4758-bc08-fddc086ed411" />


3. 复制 token ，将token 添加在请求头中，例如
<img width="1838" height="1021" alt="image" src="https://github.com/user-attachments/assets/df911d7a-d3d0-44dc-b3c6-58607ff3807d" />


```json
{
  "mcpServers": {
    "smartdb": {
      "name": "smartdb",
      "type": "streamableHttp",
      "description": "",
      "isActive": true,
      "url": "http://localhost:3000/mcp/",
      "headers": {
        "authorization": "bearer TOKEN值"
      }
    }
  }
}
```

## 使用示例
1. 查询default连接池的表数据
    <img width="1136" height="731" alt="image" src="https://github.com/user-attachments/assets/14e6adf6-f7a2-45a7-b4e6-df29cc9e2604" />

2. 查询其他连接池的表数据
   <img width="1130" height="805" alt="image" src="https://github.com/user-attachments/assets/e6419269-16c1-4a3b-aa73-d74647fe1bbd" />

3. 查询其他连接池、其他库的表数据
   <img width="1127" height="668" alt="image" src="https://github.com/user-attachments/assets/dd5cfea9-4d9b-46eb-b1cc-ad38963ed671" />

4. 修改表数据
   <img width="1138" height="696" alt="image" src="https://github.com/user-attachments/assets/930fb947-656f-41a7-93fa-2b83dd64b4ec" />

5. 数据库健康检测
   <img width="1119" height="3264" alt="image" src="https://github.com/user-attachments/assets/d065173b-140c-44f1-9ce8-16ac61562b38" />

6. sql优化
   <img width="1570" height="4107" alt="image" src="https://github.com/user-attachments/assets/594975e7-b040-4ccc-8e31-9423e6597ec2" />



