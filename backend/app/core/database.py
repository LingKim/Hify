"""Database foundation for async SQLAlchemy access."""

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from sqlalchemy import BigInteger, DateTime, Identity, Integer, MetaData, func
from sqlalchemy import select as sql_select
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)

from app.core.config import get_settings

UTC = ZoneInfo("UTC")
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(tz=UTC)


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all ORM models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Derive table names from class names."""
        return cls.__name__.lower()


class TimestampSoftDeleteMixin:
    """Shared audit and soft-delete fields."""

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    @property
    def is_deleted(self) -> bool:
        """Return whether the row has been soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark the row as deleted."""
        self.deleted_at = utc_now()

    def restore(self) -> None:
        """Restore a soft-deleted row."""
        self.deleted_at = None


@lru_cache
def get_engine() -> AsyncEngine:
    """Create and cache the async database engine."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        pool_pre_ping=settings.database_pool_pre_ping,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout_seconds,
        pool_recycle=settings.database_pool_recycle_seconds,
        connect_args={
            "timeout": settings.database_connect_timeout_seconds,
        },
    )


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create and cache the async session factory."""
    return async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        autoflush=False,
    )


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped async database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def session_scope(
    *,
    commit_on_exit: bool = False,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide an async session with explicit commit control."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            if commit_on_exit:
                await session.commit()
        except Exception:
            await session.rollback()
            raise


async def ping_database() -> bool:
    """Return whether the database connection can serve a simple query."""
    async with session_scope() as session:
        result = await session.execute(sql_select(1))
        return result.scalar_one() == 1
