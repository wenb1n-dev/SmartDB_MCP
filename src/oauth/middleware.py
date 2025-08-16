from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from oauth.token_handler import TokenHandler


class OAuthMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, exclude_paths: Optional[list[str]] = None):
        """
        初始化中间件

        Args:
            app: Starlette应用实例
            exclude_paths: 不需要认证的路径列表
        """
        super().__init__(app)
        # 默认排除路径：登录相关页面和资源
        default_exclude_paths = [
            "/login",  # 登录页面
            "/mcp/authorize",  # 登录API
        ]
        self.exclude_paths = exclude_paths or default_exclude_paths
        #self.login_url = os.getenv("MCP_LOGIN_URL", "http://localhost:3000/login")

    def _is_excluded_path(self, path: str) -> bool:
        """
        检查路径是否在排除列表中

        Args:
            path: 请求路径

        Returns:
            bool: 是否排除认证
        """
        return any(
            path == excluded or path.startswith(f"{excluded}/")
            for excluded in self.exclude_paths
        )
    async def dispatch(self, request: Request, call_next):
        """
        处理请求

        Args:
            request: 请求对象
            call_next: 下一个处理函数
        """
        # 检查是否需要跳过认证
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        # 获取认证头
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # 只在需要时弹出登录框，并且不是API请求时
            return JSONResponse(
                {"error": "invalid_request", "error_description": "Missing authorization header"},
                status_code=401
            )

        # 验证token格式
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(
                {"error": "invalid_request", "error_description": "Invalid authorization header format"},
                status_code=401
            )

        token = parts[1]

        # 验证token
        payload = TokenHandler.verify_token(token)
        if not payload:
            return JSONResponse(
                {"error": "invalid_token", "error_description": "Token is invalid or expired"},
                status_code=401
            )

        # 检查token类型
        if payload.get("type") != "access_token":
            return JSONResponse(
                {"error": "invalid_token", "error_description": "Invalid token type"},
                status_code=401
            )

        # 将用户信息添加到请求对象
        request.state.user = {
            "id": payload["sub"],
            "username": payload["username"]
        }

        return await call_next(request)