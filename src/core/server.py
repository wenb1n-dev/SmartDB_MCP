import asyncio
import contextlib
import os

from collections.abc import AsyncIterator
from starlette.responses import Response

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
from connection.MultiDBPoolManager import MultiDBPoolManager
from core.handles.ToolHandler import ToolRegistry

# 初始化服务器
app = Server("SmartDB_MCP")


@app.list_tools()
async def list_tools() -> list[Tool]:
    print("正在初始化工具...")

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
    # 启动时初始化全局连接池（单例）
    MultiDBPoolManager.init_from_config()
    print(f"\n✓ 成功初始化连接池管理器")

    # 使用传入的默认模式
    if mode == "stdio":
        asyncio.run(run_stdio())
    else:
        run_streamable_http(False, oauth)


if __name__ == "__main__":
    main()
