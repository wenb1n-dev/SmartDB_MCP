[![简体中文](https://img.shields.io/badge/简体中文-点击查看-orange)](README-zh.md)
[![English](https://img.shields.io/badge/English-Click-yellow)](README.md)

<img width="1023" height="270" alt="image" src="https://github.com/user-attachments/assets/4b282174-dd45-4edb-9de8-9b14e2c59a9e" />


# SmartDB

SmartDB is a universal database gateway that implements the Model Context Protocol (MCP) server interface. This gateway allows MCP-compatible clients to connect and explore different databases.

Compared to similar products, SmartDB not only provides basic database connection and exploration capabilities but also adds advanced features such as OAuth 2.0 authentication , health checks, SQL optimization, and index health detection, making database management and maintenance more secure and intelligent.

<img width="1303" height="697" alt="image" src="https://github.com/user-attachments/assets/9340f85e-28b0-45f2-8cb2-768b0d1c8b5c" />


## Currently Supported Databases
| Database | Support | Description |
|----------|---------|-------------|
| MySQL | √ | Supports MySQL 5.6+, MariaDB 10+ |
| PostgreSQL | √ | Supports PostgreSQL 9.6+, YMatrix |
| Oracle | √ | Oracle 12+ |
| SQL Server | √ | Microsoft SQL Server 2012+ |

## Tool List
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

## Usage

### Environment Configuration File Description
```bash
# Database configuration file path
DATABASE_CONFIG_FILE=/Volumes/SmartDB/src/config/database_config.json

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
  }
}
```

* Database Connection Parameter Description

The following table details the meaning and usage of each parameter in the database connection configuration file:

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| host | Yes | string | Database server address |
| port | Yes | integer | Database server port number |
| user | Yes | string | Database username |
| password | Yes | string | Database user password |
| database | Yes | string | Database name to connect to |
| role | Yes | string | User role, such as "readonly" for read-only permissions |
| pool_size | Yes | integer | Connection pool size |
| max_overflow | Yes | integer | Maximum overflow connections in connection pool |
| pool_recycle | Yes | integer | Connection pool recycle time (seconds) |
| pool_timeout | Yes | integer | Connection pool timeout time (seconds) |
| type | Yes | string | Database type, such as "mysql", "postgresql", "oracle", "mssqlserver" |

* Additional Parameters for Specific Databases

| Parameter | Database Type | Required | Type | Description |
|-----------|---------------|----------|------|-------------|
| schema | PostgreSQL, SQL Server | No | string | Database schema |
| service_name | Oracle | No | string | Oracle service name |

* role permission control configuration items and corresponding database permissions: readonly (readonly), read/write (writer), administrator (admin)
```
    "readonly": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"],  # readonly permission
    "writer": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE"],  # read/write permission
    "admin": ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE", 
             "CREATE", "ALTER", "DROP", "TRUNCATE"]  # administrator permission
```

* Note

"default" is the default database connection configuration and must be configured. Other database configurations should be added as needed.

## pip installation and configuration

```bash
pip install SmartDB-MCP

Parameter explanation
--mode: transmission mode ("stdio", "sse", "streamablehttp")
--envfile path of the environment variable file
--oauth enable oauth authentication (currently only supported in "streamablehttp" mode)

Start command:
 smartdb --envfile=/Volumes/config/.env --oauth=true


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
uv run -m mysql_mcp_server_pro.server --mode sse

# Custom env file location
uv run -m mysql_mcp_server_pro.server --mode sse --envfile /path/to/.env
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

   
   
