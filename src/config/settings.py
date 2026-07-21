"""Unified application settings using pydantic-settings.

Consolidates all environment-variable-driven configuration into a single
``Settings`` class. Components should read configuration via
``get_settings()`` instead of calling ``os.getenv`` directly.

Usage::

    from config.settings import get_settings

    settings = get_settings()
    host = settings.server_host
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Unified application settings.

    All fields are populated from environment variables (case-insensitive).
    The ``.env`` file should be loaded via ``python-dotenv`` before
    ``get_settings()`` is first called (see ``core.server.main``).
    """

    model_config = SettingsConfigDict(
        env_file=None,          # env file is loaded explicitly by server.py
        case_sensitive=False,
        extra="ignore",
    )

    # Server configuration
    server_host: str = "0.0.0.0"
    server_port: int = 3000

    # Database configuration file path
    database_config_file: str = ""

    # OAuth 2.0 configuration
    client_id: str = ""
    client_secret: str = ""
    token_secret_key: str = ""
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    oauth_user_name: str = "admin"
    oauth_user_password: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton.

    The first call reads the current environment; subsequent calls return
    the cached instance. Call ``get_settings.cache_clear()`` to force a
    refresh (useful in tests).
    """
    return Settings()
