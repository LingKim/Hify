import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import Base, TimestampSoftDeleteMixin, get_db_session


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
    assert hasattr(TimestampSoftDeleteMixin, "created_at")
    assert hasattr(TimestampSoftDeleteMixin, "updated_at")
    assert hasattr(TimestampSoftDeleteMixin, "deleted_at")


def test_alembic_can_load_metadata() -> None:
    from alembic.config import Config

    config = Config("alembic.ini")

    assert config.get_main_option("script_location") == "alembic"
