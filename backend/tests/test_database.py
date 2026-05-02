import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.model import User
from app.core.config import get_settings
from app.core.database import Base, TimestampSoftDeleteMixin, get_db_session
from app.core.repository import AsyncRepository


@pytest.mark.asyncio
async def test_get_db_session_yields_async_session() -> None:
    session_generator = get_db_session()

    session = await anext(session_generator)

    assert isinstance(session, AsyncSession)

    with pytest.raises(StopAsyncIteration):
        await anext(session_generator)


def test_settings_reads_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://tester:secret@localhost:5432/hify",
    )
    get_settings.cache_clear()

    settings = get_settings()

    assert (
        settings.database_url
        == "postgresql+asyncpg://tester:secret@localhost:5432/hify"
    )

    get_settings.cache_clear()


def test_base_metadata_and_common_mixin_are_available() -> None:
    assert Base.metadata is not None
    assert Base.metadata.naming_convention is not None
    assert hasattr(TimestampSoftDeleteMixin, "created_at")
    assert hasattr(TimestampSoftDeleteMixin, "updated_at")
    assert hasattr(TimestampSoftDeleteMixin, "deleted_at")
    assert hasattr(TimestampSoftDeleteMixin, "version")


def test_alembic_can_load_metadata() -> None:
    from alembic.config import Config

    config = Config("alembic.ini")

    assert config.get_main_option("script_location") == "alembic"


class FakeRepositorySession:
    def __init__(self) -> None:
        self.statement = None
        self.entity = None
        self.flush_called = False

    async def scalar(self, statement):  # type: ignore[no-untyped-def]
        self.statement = statement
        return None

    def add(self, entity: object) -> None:
        self.entity = entity

    async def flush(self) -> None:
        self.flush_called = True


@pytest.mark.asyncio
async def test_async_repository_filters_soft_deleted_rows() -> None:
    session = FakeRepositorySession()
    repository = AsyncRepository(session, User)

    await repository.get_by_id(1)

    assert session.statement is not None
    compiled = str(
        session.statement.compile(compile_kwargs={"literal_binds": True})
    )
    assert "users.id = 1" in compiled
    assert "users.deleted_at IS NULL" in compiled


@pytest.mark.asyncio
async def test_async_repository_add_flushes_entity() -> None:
    session = FakeRepositorySession()
    repository = AsyncRepository(session, User)
    user = User(
        username="demo",
        email="demo@example.com",
        password_hash="hashed",
    )

    created = await repository.add(user)

    assert created is user
    assert session.entity is user
    assert session.flush_called is True
