"""Minimal repository helpers for business modules."""

from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import TimestampSoftDeleteMixin


class AsyncRepository[ModelT]:
    """Shared SQLAlchemy repository with soft-delete defaults."""

    def __init__(
        self,
        session: AsyncSession | Any,
        model_type: type[ModelT],
    ) -> None:
        self.session = session
        self.model_type: Any = model_type

    async def get_by_id(
        self,
        entity_id: int,
        *,
        include_deleted: bool = False,
    ) -> ModelT | None:
        """Return an entity by id, excluding soft-deleted rows by default."""
        statement = self._build_select(include_deleted=include_deleted).where(
            self.model_type.id == entity_id
        )
        return await self.session.scalar(statement)

    async def add(self, entity: ModelT) -> ModelT:
        """Add an entity to the current session and flush it."""
        self.session.add(entity)
        await self.session.flush()
        return entity

    def _build_select(self, *, include_deleted: bool) -> Select[tuple[ModelT]]:
        statement = select(self.model_type)
        if not include_deleted and issubclass(
            self.model_type,
            TimestampSoftDeleteMixin,
        ):
            statement = statement.where(self.model_type.deleted_at.is_(None))
        return statement
