[![简体中文](https://img.shields.io/badge/简体中文-点击查看-orange)](README-zh.md)
[![English](https://img.shields.io/badge/English-Click-yellow)](README.md)
[![MseeP.ai Security Assessment Badge](https://mseep.net/mseep-audited.png)](https://mseep.ai/app/wenb1n-dev-smartdb-mcp)

<img width="1023" height="270" alt="image" src="https://github.com/user-attachments/assets/4b282174-dd45-4edb-9de8-9b14e2c59a9e" />


# SmartDB

SmartDB is a universal multi-paradigm data-infrastructure gateway that implements the Model Context Protocol (MCP) server interface. This gateway allows MCP-compatible clients to connect and explore different data sources in a unified way.

It currently covers **6 data paradigms and 10 data sources**: 5 relational databases (MySQL, PostgreSQL, Oracle, SQL Server, Dameng), KV store (Redis), document store (MongoDB), vector database (Milvus), search engine (Elasticsearch), and message queue (Apache Kafka), with 26 MCP tools in total. Tools are dynamically filtered and exposed according to the paradigm of each connection pool.

Compared to similar products, SmartDB not only provides basic database connection and exploration capabilities but also adds advanced features such as OAuth 2.0 authentication, health checks, SQL optimization, and index health detection, making database management and maintenance more secure and intelligent.

<img width="3000" height="1660" alt="SmartDB 数据源支持简图（手绘风高清位图）" src="https://github.com/user-attachments/assets/0004295e-d653-43d4-af1f-35b5e98ac184" />



## Currently Supported Databases
| Database   | Type | Support | Description              |
|------------|------|---------|--------------------------|
| MySQL      | Relational | √ | Supports MySQL 5.6+, MariaDB 10+ |
| PostgreSQL | Relational | √ | Supports PostgreSQL 9.6+, YMatrix |
| Oracle     | Relational | √ | Oracle 12+               |
| SQL Server | Relational | √ | Microsoft SQL Server 2012+ |
| Dameng     | Relational | √ | Dameng 8.0+              |
| Redis      | KV Store | √ | Redis 5.0+              |
| MongoDB    | Document | √ | MongoDB 4.0+            |
| Milvus     | Vector | √ | Milvus 2.3+             |
| Elasticsearch | Search Engine | √ | Python driver ≥ 8.0, auto-adapts to ES 7/8/9 servers |
| Apache Kafka | Message Queue | √ | kafka-python-ng driver ≥ 2.2.2 |

## Tool List

There are 26 tools in total. `get_db_health` and `get_db_version` are universal tools available for every data source; the other tools are exposed according to the paradigm of the connection pool.

### Relational Database Tools
| Tool Name | Description                                                                                                                                                                                   |
|-----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| execute_sql | SQL execution tool that can execute ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "TRUNCATE"] commands based on permission configuration |
| get_db_health | Analyzes database health status (connection status, transaction status, running status, lock detection) and outputs professional diagnostic reports and solutions                             |
| get_table_desc | Searches for table structures in the database based on table names, supports multi-table queries                                                                                              |
| get_table_index | Searches for table indexes in the database based on table names, supports multi-table queries                                                                                                 |
| get_table_name | Database table name query tool. Used to query all table names in the database or search for corresponding table names based on Chinese table names or table descriptions                      |
| get_db_version | Database version query tool                                                                                                                                                                   |
| sql_creator | SQL query generation tool that generates corresponding SQL query statements based on different database types                                                                                 |
| sql_optimize | A professional SQL performance optimization tool that provides expert optimization suggestions based on execution plans, table structure information, table data volume, and table indexes.   |

### KV Store Tools (Redis)
| Tool Name | Description |
|-----------|-------------|
| execute_command | Execute Redis commands (GET/SET/HGET/LPUSH etc.) with permission enforcement |
| get_key_info | Query Redis key details (type, size, TTL, memory usage) |
| scan_keys | Scan Redis keys by pattern using SCAN command (non-blocking) |
| get_db_health | Analyze Redis health (connection, memory, slowlog, replication, persistence) |
| get_db_version | Query Redis version |

### Document Store Tools (MongoDB)
| Tool Name | Description |
|-----------|-------------|
| execute_mongo_query | Execute MongoDB queries (find/aggregate) with filter, projection, sort, pagination |
| execute_mongo_write | Execute MongoDB writes (insert_one/insert_many/update_one/update_many/replace_one/delete_one/delete_many) with permission enforcement; supports Extended JSON ($oid/$date); update_many/delete_many require an explicit filter |
| get_collection_schema | Infer collection schema by sampling documents (field names, types, presence) |
| get_collection_names | List collections in a MongoDB database, with optional name pattern filter |
| get_collection_indexes | Query index information for a MongoDB collection or all collections |
| mongo_explain | Analyze MongoDB query execution plan (explain), including query planner and execution stats |
| get_db_health | Analyze MongoDB health (connection, memory, slowlog, replication, indexes) |
| get_db_version | Query MongoDB version |

### Vector Store Tools (Milvus)
| Tool Name | Description |
|-----------|-------------|
| execute_vector_search | Execute vector similarity search on a collection, returning top-K nearest neighbors |
| get_collection_info | Query vector collection metadata (dimension, metric type, schema, entity count) |
| get_vector_index_info | Query vector index information (index type, parameters, build progress) |
| get_db_health | Analyze Milvus health (connection, memory, indexes, latency, nodes) |
| get_db_version | Query Milvus version |

### Search Engine Tools (Elasticsearch)
| Tool Name | Description |
|-----------|-------------|
| execute_es_query | Execute Elasticsearch DSL queries (search/count/aggregate) with full DSL support |
| get_index_mapping | Query index mappings (field types, analyzers) and settings |
| get_index_names | List Elasticsearch indices |
| get_db_health | Analyze Elasticsearch health (cluster status, shards, nodes) |
| get_db_version | Query Elasticsearch version |

### Message Queue Tools (Apache Kafka)
| Tool Name | Description |
|-----------|-------------|
| list_topics | List Kafka topics |
| get_topic_info | Query topic details: partitions, leader, replicas, offsets |
| get_consumer_lag | Query consumer group lag |
| get_db_health | Analyze Kafka health (brokers, topics/partitions, ISR, consumer groups) |
| get_db_version | Query Kafka cluster version and broker metadata |

## Usage

### Environment Configuration File Description
```bash
# Database configuration file path
DATABASE_CONFIG_FILE=/Volumes/SmartDB/src/config/database_config.json

#========Server========
# Server listen host
SERVER_HOST=0.0.0.0
# Server listen port
SERVER_PORT=3000

#========OAuth2========
# OAuth2 client ID
CLIENT_ID=smart_db_client_id
# OAuth2 client secret
CLIENT_SECRET=smart_db_client_secret
# Access token expiration time (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30
# Refresh token expiration time (days)
REFRESH_TOKEN_EXPIRE_DAYS=30
# Token encryption key
TOKEN_SECRET_KEY=smart_db_token_secret
# Username
OAUTH_USER_NAME=admin
# Password
OAUTH_USER_PASSWORD=wenb1n
```
Note: If you adjust the client ID and key in the oauth configuration, please also modify the corresponding configuration in the static/config file in the previous code

### Database Connection Configuration Description
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

> For Elasticsearch and Kafka, `user`/`password` are optional: omit them for clusters without authentication. Kafka uses SASL/PLAIN when both are provided. A ready-to-use template is available at `src/config/database_config.example.json`.

* Database Connection Parameter Description

The following table details the meaning and usage of each parameter in the database connection configuration file:

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| host | Yes | string | Database server address |
| port | Yes | integer | Database server port number |
| user | Relational, MongoDB, Milvus; optional for Elasticsearch, Kafka (no-auth clusters) | string | Database username |
| password | Relational, MongoDB, Milvus; optional for Elasticsearch, Kafka (no-auth clusters) | string | Database user password |
| database | Relational, MongoDB, Milvus | string | Database name to connect to |
| role | Yes | string | User role, such as "readonly" for read-only permissions |
| pool_size | Yes | integer | Connection pool size |
| max_overflow | Relational | integer | Maximum overflow connections in connection pool |
| pool_recycle | Relational | integer | Connection pool recycle time (seconds) |
| pool_timeout | Relational | integer | Connection pool timeout time (seconds) |
| type | Yes | string | Database type: "mysql", "postgresql", "oracle", "mssqlserver", "dameng", "redis", "mongodb", "milvus", "elasticsearch", "kafka" |

* Additional Parameters for Specific Databases

| Parameter | Database Type | Required | Type | Description |
|-----------|---------------|----------|------|-------------|
| schema | PostgreSQL, SQL Server | No | string | Database schema |
| service_name | Oracle | No | string | Oracle service name |
| db | Redis | No | integer | Redis database index, default 0 |
| auth_source | MongoDB | No | string | Authentication database, default "admin" |
| min_pool_size | MongoDB | No | integer | Minimum pool size, default 5 |
| token | Milvus | No | string | Authentication token (alternative to user/password) |
| use_ssl | Elasticsearch | No | boolean | Whether to connect over HTTPS, default false |
| verify_certs | Elasticsearch | No | boolean | Whether to verify TLS certificates, default true |

* Role permission control configuration: readonly / writer / admin. For relational databases the role maps to SQL operation categories as follows:
```
    "readonly": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"],  # readonly permission
    "writer": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE"],  # read/write permission
    "admin": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE",
             "CREATE", "ALTER", "DROP", "TRUNCATE"]  # administrator permission
```
For non-relational data sources (Redis, MongoDB, Milvus, Elasticsearch, Kafka), the same three roles are enforced via a READ / WRITE / ADMIN / DANGEROUS category-based permission policy. For example, a `readonly` role is rejected when calling `execute_mongo_write`, Redis write commands, etc.

* Note

"default" is the default database connection configuration and must be configured. Other database configurations should be added as needed.

## pip installation and configuration

```bash
pip install SmartDB-MCP
```

Parameter explanation:

- `--mode`: transmission mode (`stdio`, `sse`, `streamablehttp`)
- `--envfile`: path of the environment variable file
- `--oauth`: enable OAuth authentication (currently only supported in `streamablehttp` mode)

Start command:

```bash
smartdb --envfile=/path/to/.env --oauth=true
```

## Docker Startup

### Quick Start

#### 1. Build and Start Service

```bash
# Start service using docker-compose
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f smartdb
```

#### 2. Manual Image Building

```bash
# Build image
docker build -t smartdb-mcp:latest .

# Run container
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

## Code Startup

### Local Development Streamable Http Mode

- Start service using uv

Add the following content to your MCP client tools, such as cursor, cline, etc.

MCP JSON as follows:
```json
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
```

Start command:
```bash
# Download dependencies
uv sync

# Start
uv run -m core.server

# Custom env file location
uv run -m core.server --envfile /path/to/.env
```

### Local Development SSE Mode

- Start service using uv

Add the following content to your MCP client tools, such as cursor, cline, etc.

MCP JSON as follows:
```json
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
```

Start command:
```bash
# Download dependencies
uv sync

# Start
uv run -m core.server --mode sse

# Custom env file location
uv run -m core.server --mode sse --envfile /path/to/.env
```

### Local Development STDIO Mode

Add the following content to your MCP client tools, such as cursor, cline, etc.

MCP JSON as follows:
```json
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

## OAuth 2.0 Authentication Support

1. Start authentication service. By default, it uses the built-in OAuth 2.0 password mode authentication. You can modify your own authentication service address in the env file.
```bash
uv run -m core.server --oauth=true
```

2. Access the authentication service at http://localhost:3000/login. Default account and password are configured in the env file.
<img width="1777" height="950" alt="image" src="https://github.com/user-attachments/assets/20531bee-467f-4758-bc08-fddc086ed411" />


3. Copy the token and add it to the request header, for example:
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
        "authorization": "bearer TOKEN_VALUE"
      }
    }
  }
}
```

## Usage Examples
1. Query the table data of the default connection pool
<img width="1131" height="1112" alt="image" src="https://github.com/user-attachments/assets/a858a38a-c57e-47a6-8f74-2458266859ac" />

2. Query the table data of the others connection pool
<img width="1144" height="728" alt="image" src="https://github.com/user-attachments/assets/ad619912-9aad-4e10-b4aa-b1de521390c2" />

3. Query data from tables in other connection pools and other databases
<img width="1128" height="586" alt="image" src="https://github.com/user-attachments/assets/f110f00f-319b-4754-ae4c-32fee0d2a44d" />

4. Query database health status
<img width="1140" height="2560" alt="image" src="https://github.com/user-attachments/assets/fa55271c-94ad-4079-a9eb-c68a8e607111" />

5. Sql Optimize
<img width="1554" height="3613" alt="image" src="https://github.com/user-attachments/assets/58d9c835-160c-44b3-b97c-0e46830ea438" />

   
   
