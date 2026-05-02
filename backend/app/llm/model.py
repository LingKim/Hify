"""LLM module ORM models."""

from typing import ClassVar

from app.core.database import Base, TimestampSoftDeleteMixin


class LlmModel(TimestampSoftDeleteMixin, Base):
    """Placeholder model configuration entity for future LLM persistence."""

    __tablename__: ClassVar[str] = "llm_models"
