"""Application configuration."""

from dataclasses import dataclass
from functools import lru_cache
from os import getenv

DEFAULT_APP_NAME = "Hify Backend"
DEFAULT_APP_VERSION = "0.1.0"
DEFAULT_APP_ENV = "development"
DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/hify"
)
DEFAULT_DATABASE_POOL_SIZE = 10
DEFAULT_DATABASE_MAX_OVERFLOW = 20
DEFAULT_DATABASE_POOL_TIMEOUT_SECONDS = 30
DEFAULT_DATABASE_POOL_RECYCLE_SECONDS = 1800
DEFAULT_DATABASE_CONNECT_TIMEOUT_SECONDS = 10.0
DEFAULT_REDIS_KEY_PREFIX = "hify"
DEFAULT_REDIS_DEFAULT_TTL_SECONDS = 300
DEFAULT_JWT_SECRET_KEY = "hify-dev-secret-key-with-32-bytes"
DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_JWT_ACCESS_TOKEN_TTL_SECONDS = 3600
DEFAULT_JWT_ISSUER = "hify-backend"
DEFAULT_HTTP_CLIENT_TIMEOUT_SECONDS = 15.0
DEFAULT_HTTP_CLIENT_MAX_RETRIES = 2
DEFAULT_HTTP_CLIENT_RETRY_BACKOFF_SECONDS = 0.2
DEFAULT_HTTP_CLIENT_USER_AGENT = "hify-backend/0.1.0"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_DISTRIBUTED_LOCK_PREFIX = "hify-lock"
DEFAULT_DISTRIBUTED_LOCK_TTL_SECONDS = 30
DEFAULT_IDEMPOTENCY_TTL_SECONDS = 300


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings loaded from environment variables."""

    app_name: str = DEFAULT_APP_NAME
    app_version: str = DEFAULT_APP_VERSION
    app_env: str = DEFAULT_APP_ENV
    database_url: str = DEFAULT_DATABASE_URL
    database_echo: bool = False
    database_pool_pre_ping: bool = True
    database_pool_size: int = DEFAULT_DATABASE_POOL_SIZE
    database_max_overflow: int = DEFAULT_DATABASE_MAX_OVERFLOW
    database_pool_timeout_seconds: int = DEFAULT_DATABASE_POOL_TIMEOUT_SECONDS
    database_pool_recycle_seconds: int = (
        DEFAULT_DATABASE_POOL_RECYCLE_SECONDS
    )
    database_connect_timeout_seconds: float = (
        DEFAULT_DATABASE_CONNECT_TIMEOUT_SECONDS
    )
    redis_url: str | None = None
    redis_enabled: bool = False
    redis_key_prefix: str = DEFAULT_REDIS_KEY_PREFIX
    redis_default_ttl_seconds: int = DEFAULT_REDIS_DEFAULT_TTL_SECONDS
    jwt_secret_key: str = DEFAULT_JWT_SECRET_KEY
    jwt_algorithm: str = DEFAULT_JWT_ALGORITHM
    jwt_access_token_ttl_seconds: int = (
        DEFAULT_JWT_ACCESS_TOKEN_TTL_SECONDS
    )
    jwt_issuer: str = DEFAULT_JWT_ISSUER
    http_client_timeout_seconds: float = (
        DEFAULT_HTTP_CLIENT_TIMEOUT_SECONDS
    )
    http_client_max_retries: int = DEFAULT_HTTP_CLIENT_MAX_RETRIES
    http_client_retry_backoff_seconds: float = (
        DEFAULT_HTTP_CLIENT_RETRY_BACKOFF_SECONDS
    )
    http_client_user_agent: str = DEFAULT_HTTP_CLIENT_USER_AGENT
    log_level: str = DEFAULT_LOG_LEVEL
    distributed_lock_prefix: str = DEFAULT_DISTRIBUTED_LOCK_PREFIX
    distributed_lock_ttl_seconds: int = DEFAULT_DISTRIBUTED_LOCK_TTL_SECONDS
    idempotency_ttl_seconds: int = DEFAULT_IDEMPOTENCY_TTL_SECONDS

    @classmethod
    def from_env(cls) -> "Settings":
        """Create a settings object from environment variables."""
        return cls(
            app_name=getenv("APP_NAME", DEFAULT_APP_NAME),
            app_version=getenv("APP_VERSION", DEFAULT_APP_VERSION),
            app_env=getenv("APP_ENV", DEFAULT_APP_ENV),
            database_url=getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
            database_echo=getenv("DATABASE_ECHO", "false").lower() == "true",
            database_pool_pre_ping=(
                getenv("DATABASE_POOL_PRE_PING", "true").lower() == "true"
            ),
            database_pool_size=int(
                getenv(
                    "DATABASE_POOL_SIZE",
                    str(DEFAULT_DATABASE_POOL_SIZE),
                )
            ),
            database_max_overflow=int(
                getenv(
                    "DATABASE_MAX_OVERFLOW",
                    str(DEFAULT_DATABASE_MAX_OVERFLOW),
                )
            ),
            database_pool_timeout_seconds=int(
                getenv(
                    "DATABASE_POOL_TIMEOUT_SECONDS",
                    str(DEFAULT_DATABASE_POOL_TIMEOUT_SECONDS),
                )
            ),
            database_pool_recycle_seconds=int(
                getenv(
                    "DATABASE_POOL_RECYCLE_SECONDS",
                    str(DEFAULT_DATABASE_POOL_RECYCLE_SECONDS),
                )
            ),
            database_connect_timeout_seconds=float(
                getenv(
                    "DATABASE_CONNECT_TIMEOUT_SECONDS",
                    str(DEFAULT_DATABASE_CONNECT_TIMEOUT_SECONDS),
                )
            ),
            redis_url=getenv("REDIS_URL"),
            redis_enabled=getenv("REDIS_ENABLED", "false").lower() == "true",
            redis_key_prefix=getenv(
                "REDIS_KEY_PREFIX",
                DEFAULT_REDIS_KEY_PREFIX,
            ),
            redis_default_ttl_seconds=int(
                getenv(
                    "REDIS_DEFAULT_TTL_SECONDS",
                    str(DEFAULT_REDIS_DEFAULT_TTL_SECONDS),
                )
            ),
            jwt_secret_key=getenv(
                "JWT_SECRET_KEY",
                DEFAULT_JWT_SECRET_KEY,
            ),
            jwt_algorithm=getenv("JWT_ALGORITHM", DEFAULT_JWT_ALGORITHM),
            jwt_access_token_ttl_seconds=int(
                getenv(
                    "JWT_ACCESS_TOKEN_TTL_SECONDS",
                    str(DEFAULT_JWT_ACCESS_TOKEN_TTL_SECONDS),
                )
            ),
            jwt_issuer=getenv("JWT_ISSUER", DEFAULT_JWT_ISSUER),
            http_client_timeout_seconds=float(
                getenv(
                    "HTTP_CLIENT_TIMEOUT_SECONDS",
                    str(DEFAULT_HTTP_CLIENT_TIMEOUT_SECONDS),
                )
            ),
            http_client_max_retries=int(
                getenv(
                    "HTTP_CLIENT_MAX_RETRIES",
                    str(DEFAULT_HTTP_CLIENT_MAX_RETRIES),
                )
            ),
            http_client_retry_backoff_seconds=float(
                getenv(
                    "HTTP_CLIENT_RETRY_BACKOFF_SECONDS",
                    str(DEFAULT_HTTP_CLIENT_RETRY_BACKOFF_SECONDS),
                )
            ),
            http_client_user_agent=getenv(
                "HTTP_CLIENT_USER_AGENT",
                DEFAULT_HTTP_CLIENT_USER_AGENT,
            ),
            log_level=getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL),
            distributed_lock_prefix=getenv(
                "DISTRIBUTED_LOCK_PREFIX",
                DEFAULT_DISTRIBUTED_LOCK_PREFIX,
            ),
            distributed_lock_ttl_seconds=int(
                getenv(
                    "DISTRIBUTED_LOCK_TTL_SECONDS",
                    str(DEFAULT_DISTRIBUTED_LOCK_TTL_SECONDS),
                )
            ),
            idempotency_ttl_seconds=int(
                getenv(
                    "IDEMPOTENCY_TTL_SECONDS",
                    str(DEFAULT_IDEMPOTENCY_TTL_SECONDS),
                )
            ),
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings.from_env()


settings = get_settings()
