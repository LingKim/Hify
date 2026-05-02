"""Knowledge module ORM models."""

from typing import ClassVar

from app.core.database import Base, TimestampSoftDeleteMixin


class KnowledgeBase(TimestampSoftDeleteMixin, Base):
    """Placeholder knowledge base model for future persistence."""

    __tablename__: ClassVar[str] = "knowledge_bases"
