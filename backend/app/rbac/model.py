"""RBAC ORM models."""

from __future__ import annotations

from typing import ClassVar

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampSoftDeleteMixin


class Role(TimestampSoftDeleteMixin, Base):
    """A role that can be assigned to users."""

    __tablename__: ClassVar[str] = "roles"
    __table_args__ = (
        CheckConstraint("code <> ''", name="ck_roles_code_non_empty"),
        CheckConstraint("name <> ''", name="ck_roles_name_non_empty"),
        CheckConstraint(
            "status IN ('enabled', 'disabled')",
            name="ck_roles_status_allowed",
        ),
        CheckConstraint("version >= 1", name="ck_roles_version_positive"),
        Index("ix_roles_deleted_at", "deleted_at"),
        Index("ix_roles_is_system", "is_system"),
        Index("ix_roles_status", "status"),
        Index(
            "ux_roles_code_active",
            "code",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="enabled",
        server_default="enabled",
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    user_bindings: Mapped[list[UserRoleBinding]] = relationship(
        back_populates="role",
    )
    permission_bindings: Mapped[list[RolePermissionBinding]] = relationship(
        back_populates="role",
    )


class Permission(TimestampSoftDeleteMixin, Base):
    """A system-defined permission point."""

    __tablename__: ClassVar[str] = "permissions"
    __table_args__ = (
        CheckConstraint("code <> ''", name="ck_permissions_code_non_empty"),
        CheckConstraint("name <> ''", name="ck_permissions_name_non_empty"),
        CheckConstraint(
            "module <> ''",
            name="ck_permissions_module_non_empty",
        ),
        CheckConstraint(
            "action <> ''",
            name="ck_permissions_action_non_empty",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_permissions_version_positive",
        ),
        Index("ix_permissions_action", "action"),
        Index("ix_permissions_deleted_at", "deleted_at"),
        Index("ix_permissions_is_system", "is_system"),
        Index("ix_permissions_module", "module"),
        Index(
            "ux_permissions_code_active",
            "code",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    code: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    module: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    role_bindings: Mapped[list[RolePermissionBinding]] = relationship(
        back_populates="permission",
    )


class UserRoleBinding(TimestampSoftDeleteMixin, Base):
    """A user-to-role assignment."""

    __tablename__: ClassVar[str] = "user_role_bindings"
    __table_args__ = (
        CheckConstraint(
            "version >= 1",
            name="ck_user_role_bindings_version_positive",
        ),
        Index("ix_user_role_bindings_deleted_at", "deleted_at"),
        Index("ix_user_role_bindings_role_id", "role_id"),
        Index("ix_user_role_bindings_user_id", "user_id"),
        Index(
            "ux_user_role_bindings_user_role_active",
            "user_id",
            "role_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("roles.id"),
        nullable=False,
    )

    role: Mapped[Role] = relationship(back_populates="user_bindings")


class RolePermissionBinding(TimestampSoftDeleteMixin, Base):
    """A role-to-permission assignment."""

    __tablename__: ClassVar[str] = "role_permission_bindings"
    __table_args__ = (
        CheckConstraint(
            "version >= 1",
            name="ck_role_permission_bindings_version_positive",
        ),
        Index("ix_role_permission_bindings_deleted_at", "deleted_at"),
        Index("ix_role_permission_bindings_permission_id", "permission_id"),
        Index("ix_role_permission_bindings_role_id", "role_id"),
        Index(
            "ux_role_permission_bindings_role_permission_active",
            "role_id",
            "permission_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    role_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("roles.id"),
        nullable=False,
    )
    permission_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("permissions.id"),
        nullable=False,
    )

    role: Mapped[Role] = relationship(back_populates="permission_bindings")
    permission: Mapped[Permission] = relationship(
        back_populates="role_bindings",
    )
