"""Conversation module ORM models."""

from typing import ClassVar

from app.core.database import Base, TimestampSoftDeleteMixin


class Conversation(TimestampSoftDeleteMixin, Base):
    """Placeholder conversation model for future persistence."""

    __tablename__: ClassVar[str] = "conversations"
