"""Auth module ORM models."""

from datetime import datetime
from typing import ClassVar

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampSoftDeleteMixin


class User(TimestampSoftDeleteMixin, Base):
    """User entity for authentication and authorization."""

    __tablename__: ClassVar[str] = "users"
    __table_args__ = (
        CheckConstraint(
            "username <> ''",
            name="ck_users_username_non_empty",
        ),
        CheckConstraint("email <> ''", name="ck_users_email_non_empty"),
        CheckConstraint(
            "password_hash <> ''",
            name="ck_users_password_hash_non_empty",
        ),
        CheckConstraint("role <> ''", name="ck_users_role_non_empty"),
        CheckConstraint(
            "role IN ('admin', 'member')",
            name="ck_users_role_supported",
        ),
        CheckConstraint("version >= 1", name="ck_users_version_positive"),
        Index(
            "ux_users_username_active",
            "username",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "ux_users_email_active",
            "email",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    username: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
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
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
