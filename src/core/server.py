import asyncio
import contextlib
import os

from collections.abc import AsyncIterator
from starlette.responses import Response, HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.routing import Route, Mount

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

from config.event_store import InMemoryEventStore
from connection.pool_manager import MultiDBPoolManager


from tools.base import ToolRegistry

# 初始化服务器
app = Server("SmartDB_MCP")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
        列出所有可用的MySQL操作工具
    """
    return ToolRegistry.get_all_tools()


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


def run_sse():
    """运行SSE(Server-Sent Events)模式的服务器

    启动一个支持SSE的Web服务器，允许客户端通过HTTP长连接接收服务器推送的消息
    服务器默认监听0.0.0.0:3000
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
    uvicorn.run(starlette_app, host="0.0.0.0", port=3000)

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

    routes = []

    middleware = []

    if oauth:
        from oauth import OAuthMiddleware, login, login_page

        middleware.append(
            Middleware(OAuthMiddleware, exclude_paths=["/login", "/mcp/authorize"])
        )
        routes.append(Route("/login", endpoint=login_page, methods=["GET"]))
        routes.append(Route("/mcp/authorize", endpoint=login, methods=["POST"]))

        # 添加静态文件路由，用于提供Vue构建后的文件
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
        if os.path.exists(static_dir):
            routes.append(Mount("/", app=StaticFiles(directory=static_dir, html=True)))

    routes.append(Mount("/mcp", app=handle_streamable_http))

    # 创建应用实例
    starlette_app = Starlette(
        debug=True,
        routes=routes,
        middleware=middleware,
        lifespan=lifespan
    )

    config = uvicorn.Config(
        app=starlette_app,
        host="0.0.0.0",
        port=3000,
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
