"""Application configuration."""

from dataclasses import dataclass
from functools import lru_cache
from os import getenv

DEFAULT_APP_NAME = "Hify Backend"
DEFAULT_APP_VERSION = "0.1.0"
DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/hify"
)


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings loaded from environment variables."""

    app_name: str = DEFAULT_APP_NAME
    app_version: str = DEFAULT_APP_VERSION
    database_url: str = DEFAULT_DATABASE_URL
    database_echo: bool = False
    database_pool_pre_ping: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        """Create a settings object from environment variables."""
        return cls(
            app_name=getenv("APP_NAME", DEFAULT_APP_NAME),
            app_version=getenv("APP_VERSION", DEFAULT_APP_VERSION),
            database_url=getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
            database_echo=getenv("DATABASE_ECHO", "false").lower() == "true",
            database_pool_pre_ping=(
                getenv("DATABASE_POOL_PRE_PING", "true").lower() == "true"
            ),
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings.from_env()


settings = get_settings()
