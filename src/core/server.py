import asyncio
import contextlib
import os

from collections.abc import AsyncIterator
from starlette.responses import Response
from starlette.staticfiles import StaticFiles


import click
import uvicorn

from typing import Sequence, Dict, Any
from mcp.server.sse import SseServerTransport

from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.types import Tool, TextContent, Prompt, GetPromptResult

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.types import Scope, Receive, Send
from starlette.middleware import Middleware

from connection.pool_manager import MultiDBPoolManager
from tools.base import ToolRegistry
from config.event_store import InMemoryEventStore
from config.dbconfig import get_db_config_by_name
from config.settings import get_settings
from datasource.base import Paradigm
from datasource.registry import FactoryRegistry
from permission.guard import permission_guard
from permission.tool_specs import TOOL_PERMISSION_SPECS



# 初始化服务器
app = Server("SmartDB_MCP")


def _get_registered_paradigms() -> list[Paradigm]:
    """Collect all paradigms from registered connection pools.

    Returns:
        List of unique Paradigm values from all registered pools.
    """
    paradigms = []
    seen = set()
    for pool_name in MultiDBPoolManager.get_pool_names():
        try:
            db_config = get_db_config_by_name(pool_name)
            db_type = db_config.get("type")
            factory_class = FactoryRegistry._factory_classes.get(db_type)
            if factory_class and factory_class.paradigm not in seen:
                paradigms.append(factory_class.paradigm)
                seen.add(factory_class.paradigm)
        except Exception:
            continue
    return paradigms


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
        列出所有可用的工具，根据已注册连接池的范式动态过滤
    """
    paradigms = _get_registered_paradigms()
    if not paradigms:
        # Fallback: if no pools registered, show all tools
        return ToolRegistry.get_all_tools()
    return ToolRegistry.get_tools_by_paradigms(paradigms)


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """调用指定的工具执行操作

    Args:
        name (str): 工具名称
        arguments (dict): 工具参数

    Returns:
        Sequence[TextContent]: 工具执行结果

    Raises:
        ValueError: 当指定了未知的工具名称时抛出异常
    """
    tool = ToolRegistry.get_tool(name)
    permission_spec = TOOL_PERMISSION_SPECS.get(name)

    # 未声明权限的工具 fail-closed，防止新增工具绕过统一鉴权
    if permission_spec is None:
        return [TextContent(
            type="text",
            text=f"错误: 工具 '{name}' 未声明权限策略，已按安全策略拒绝执行"
        )]

    pool_name = permission_spec.resolve_pool_name(arguments or {})

    # 范式校验与权限校验都必须 fail-closed，不再因解析失败而放行
    try:
        db_config = get_db_config_by_name(pool_name)
        db_type = db_config.get("type")
        factory_class = FactoryRegistry._factory_classes.get(db_type)
        if factory_class is None:
            return [TextContent(
                type="text",
                text=f"错误: 无法识别连接池 '{pool_name}' 的数据源类型，已拒绝执行"
            )]

        pool_paradigm = factory_class.paradigm
        if not ToolRegistry.is_tool_applicable(name, pool_paradigm):
            return [TextContent(
                type="text",
                text=f"错误: 工具 '{name}' 不适用于范式 '{pool_paradigm.value}' 的数据源"
            )]

        decision = permission_guard.authorize(name, permission_spec, arguments or {})
        if not decision.allowed:
            return [TextContent(type="text", text=f"权限不足: {decision.reason}")]
    except Exception as exc:
        return [TextContent(type="text", text=f"错误: 工具调用被安全策略拒绝: {str(exc)}")]

    return await tool.run_tool(arguments)


async def run_stdio():
    """运行标准输入输出模式的服务器

    使用标准输入输出流(stdio)运行服务器，主要用于命令行交互模式

    Raises:
        Exception: 当服务器运行出错时抛出异常
    """
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        try:
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
        except Exception as e:
            print(f"服务器错误: {str(e)}")
            raise
        finally:
            # 优雅关闭：释放所有连接池资源
            try:
                MultiDBPoolManager.close_all()
            except Exception as e:
                print(f"关闭连接池时出错: {e}")


def run_sse():
    """运行SSE(Server-Sent Events)模式的服务器

    启动一个支持SSE的Web服务器，允许客户端通过HTTP长连接接收服务器推送的消息
    监听地址和端口通过 Settings (SERVER_HOST/SERVER_PORT) 配置
    """
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        """处理SSE连接请求

        Args:
            request: HTTP请求对象
        """
        async with sse.connect_sse(
                request.scope, request.receive, request._send
        ) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())
        return Response(status_code=204)

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message)
        ],
    )
    settings = get_settings()
    uvicorn.run(starlette_app, host=settings.server_host, port=settings.server_port)

def run_streamable_http(json_response: bool, oauth: bool):
    event_store = InMemoryEventStore()

    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=event_store,
        json_response=json_response,
    )

    async def handle_streamable_http(
            scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        else:
            await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            yield
        # 优雅关闭：释放所有连接池资源
        try:
            MultiDBPoolManager.close_all()
        except Exception as e:
            print(f"关闭连接池时出错: {e}")

    routes = []

    middleware = []

    if oauth:
        from oauth import OAuthMiddleware, login, login_page

        middleware.append(
            Middleware(OAuthMiddleware, exclude_paths=["/login", "/mcp/authorize"])
        )
        routes.append(Route("/login", endpoint=login_page, methods=["GET"]))
        routes.append(Route("/mcp/authorize", endpoint=login, methods=["POST"]))

    routes.append(Mount("/mcp", app=handle_streamable_http))

    if oauth:
        # 添加静态文件路由，用于提供Vue构建后的文件
        # 在打包后的环境中，静态文件位于site-packages/static/目录下
        static_dir = None
        try:
            # 尝试从包资源中获取静态文件路径
            import importlib.resources
            static_path = importlib.resources.files('static')

            # 尝试多种方法获取实际路径
            static_dir = None
            if hasattr(static_path, '__fspath__'):
                static_dir = static_path.__fspath__()
            elif hasattr(static_path, '_path'):
                static_dir = static_path._path
            elif hasattr(static_path, '_paths') and static_path._paths:
                static_dir = static_path._paths[0]
            else:
                # 如果都失败了，直接使用字符串转换
                static_dir = str(static_path)
                # 移除可能的 MultiplexedPath 前缀
                if 'MultiplexedPath(' in static_dir:
                    static_dir = static_dir.split('MultiplexedPath(')[1].split(')')[0]

            if os.path.exists(static_dir):
                routes.append(Mount("/", app=StaticFiles(directory=static_dir, html=True)))
        except Exception:
            # 如果包资源方式失败，尝试直接使用site-packages路径
            import sys
            for path in sys.path:
                if 'site-packages' in path:
                    static_dir = os.path.join(path, 'static')
                    if os.path.exists(static_dir):
                        routes.append(Mount("/", app=StaticFiles(directory=static_dir, html=True)))
                        break
            else:
                # 如果都失败了，尝试相对路径
                static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
                if os.path.exists(static_dir):
                    routes.append(Mount("/", app=StaticFiles(directory=static_dir, html=True)))

    # 创建应用实例
    starlette_app = Starlette(
        debug=True,
        routes=routes,
        middleware=middleware,
        lifespan=lifespan
    )

    settings = get_settings()
    config = uvicorn.Config(
        app=starlette_app,
        host=settings.server_host,
        port=settings.server_port,
        lifespan="on"
    )

    server = uvicorn.Server(config)
    server.run()

@click.command()
@click.option("--envfile", default=None, help="env file path")
@click.option("--mode", default="streamable_http", help="mode type")
@click.option("--oauth", default=False, help="open oauth")
def main(mode, envfile, oauth):
    from dotenv import load_dotenv

    # 优先加载指定的env文件
    if envfile:
        load_dotenv(envfile)
    else:
        # 获取当前文件（server.py）所在目录的绝对路径
        core_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取项目src目录路径
        src_dir = os.path.dirname(core_dir)
        # 拼接出 src/config/.env 的绝对路径
        env_path = os.path.join(src_dir, "config", ".env")
        load_dotenv(env_path)

    # env 文件已加载，清空 Settings 缓存确保后续读取最新值
    get_settings.cache_clear()

    # 启动时初始化全局连接池（单例）
    MultiDBPoolManager.init_from_config()
    print("---pool names-->",MultiDBPoolManager.get_pool_names())
    print(f"\n✓ 成功初始化连接池管理器")

    # 使用传入的默认模式
    if mode == "stdio":
        asyncio.run(run_stdio())
    elif mode == "sse":
        run_sse()
    else:
        run_streamable_http(False,oauth)


if __name__ == "__main__":
    main()
