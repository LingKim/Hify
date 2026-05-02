"""Agent module ORM models."""

from typing import ClassVar

from app.core.database import Base, TimestampSoftDeleteMixin


class Agent(TimestampSoftDeleteMixin, Base):
    """Placeholder agent model for future agent persistence."""

    __tablename__: ClassVar[str] = "agents"
