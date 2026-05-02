"""Tool module ORM models."""

from typing import ClassVar

from app.core.database import Base, TimestampSoftDeleteMixin


class Tool(TimestampSoftDeleteMixin, Base):
    """Placeholder tool definition model for future persistence."""

    __tablename__: ClassVar[str] = "tools"
