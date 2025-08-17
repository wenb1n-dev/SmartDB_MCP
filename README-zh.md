[![简体中文](https://img.shields.io/badge/简体中文-点击查看-orange)](README-zh.md)
[![English](https://img.shields.io/badge/English-Click-yellow)](README.md)

<img width="1023" height="270" alt="image" src="https://github.com/user-attachments/assets/4b282174-dd45-4edb-9de8-9b14e2c59a9e" />

# SmartDB

SmartDB是一个通用数据库网关，实现了模型上下文协议（Model Context Protocol，简称MCP）服务器接口。这个网关允许与MCP兼容的客户端连接并探索不同的数据库。

与同类产品相比，SmartDB不仅提供基本的数据库连接和探索功能，还增加了OAuth2.0认证、健康检查、SQL优化和索引健康检测等高级功能，使数据库管理和维护更加安全、智能化。

<img width="1295" height="685" alt="image" src="https://github.com/user-attachments/assets/3c06b0f7-11a8-444e-a50a-9e616af16467" />


# 目前支持的数据库
| 数据库 | 支持 | 描述                          |
|-----|----|-----------------------------|
| MySQL | √  | Mysql 5.6+、Mariadb 10+ 均支持  |
| PostgreSQL | √  | PostgreSQL 9.6+、YMatrix 均支持 |
| Oracle | √  | Oracle 12 +                 |
| SQL Server | √  | Microsoft SQL Server 2012 + |

# 工具列表
| 工具名称                  | 描述                                                                                                                                 |
|-----------------------|------------------------------------------------------------------------------------------------------------------------------------| 
| execute_sql           | sql执行工具，根据权限配置可执行["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "TRUNCATE"] 命令 |
| get_db_health | 分析数据库的健康状态（连接情况、事务情况、运行情况、锁情况检测），输出专业的诊断报告及解决方案                                                                                    |
| get_table_desc        | 根据表名搜索数据库中对应的表结构,支持多表查询                                                                                                            |
| get_table_index       | 根据表名搜索数据库中对应的表索引,支持多表查询                                                                                                            |
| get_table_name        | 数据库表名查询工具。用于查询数据库中的所有表名或将根据表的中文名称或表描述搜索数据库中对应的表名                                                                                   |
| get_db_version | 数据库版本查询工具                                                                                                                          |
| sql_creator | SQL查询生成工具，根据不同的数据库类型生成对应SQL查询语句                                                                                                    


# 使用方法
## env 配置文件说明
```aiignore
# 数据库配置文件路径
DATABASE_CONFIG_FILE=/Volumes/SmartDB/src/config/database_config.json

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
  }
}

```
* 数据库连接参数说明

下表详细说明了数据库连接配置文件中各参数的含义和用法：

| 参数名 | 必需 | 类型 | 描述 |
|--------|------|------|------|
| host | 是 | string | 数据库服务器地址 |
| port | 是 | integer | 数据库服务器端口号 |
| user | 是 | string | 数据库用户名 |
| password | 是 | string | 数据库用户密码 |
| database | 是 | string | 要连接的数据库名称 |
| role | 是 | string | 用户角色，如 "readonly" 表示只读权限 |
| pool_size | 是 | integer | 连接池大小 |
| max_overflow | 是 | integer | 连接池最大溢出连接数 |
| pool_recycle | 是 | integer | 连接池回收时间（秒） |
| pool_timeout | 是 | integer | 连接池超时时间（秒） |
| type | 是 | string | 数据库类型，如 "mysql"、"postgresql"、"oracle"、"mssqlserver" |

* 特定数据库额外参数

| 参数名 | 数据库类型 | 必需 | 类型 | 描述 |
|--------|------------|------|------|------|
| schema | PostgreSQL, SQL Server | 否 | string | 数据库模式 |
| service_name | Oracle | 否 | string | Oracle服务名 |

* 注意

default 为默认数据库连接配置，必须配置，其他数据库配置请自行添加 

## docker 启动
### 快速开始

#### 1. 构建并启动服务

```bash
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
      "url": "http://localhost:9000/sse"
    }
  }
}
````

启动命令
```
# 下载依赖
uv sync

# 启动
uv run -m mysql_mcp_server_pro.server --mode sse

# 自定义env文件位置
uv run -m mysql_mcp_server_pro.server --mode sse --envfile /path/to/.env
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


