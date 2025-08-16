from typing import ClassVar, Optional
from pydantic_settings import BaseSettings


class OAuthConfig(BaseSettings):

    TOKEN_ALGORITHM: ClassVar[str] = "HS256"

    # 允许的授权类型
    GRANT_TYPES: ClassVar[list[str]]= ["password", "refresh_token"]