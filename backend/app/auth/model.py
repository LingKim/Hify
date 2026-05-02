"""Auth module ORM models."""

from typing import ClassVar

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampSoftDeleteMixin


class User(TimestampSoftDeleteMixin, Base):
    """User entity for authentication and authorization."""

    __tablename__: ClassVar[str] = "users"

    username: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="member",
        server_default="member",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
