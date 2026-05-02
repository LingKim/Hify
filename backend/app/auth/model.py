"""Auth module ORM models."""

from typing import ClassVar

from app.core.database import Base, TimestampSoftDeleteMixin


class User(TimestampSoftDeleteMixin, Base):
    """Placeholder user model for future auth persistence."""

    __tablename__: ClassVar[str] = "users"
