"""Seed or reset the local development root user."""

import asyncio

from sqlalchemy import select

from app.auth.model import User
from app.auth.password import hash_password
from app.core.database import session_scope
from app.rbac.model import Role, UserRoleBinding

ROOT_USERNAME = "root"
ROOT_EMAIL = "root@hify.local"
ROOT_PASSWORD = "123456"


async def main() -> None:
    """Create or reset the local root administrator account."""
    async with session_scope(commit_on_exit=True) as session:
        admin_role = await session.scalar(
            select(Role).where(
                Role.code == "admin",
                Role.deleted_at.is_(None),
            )
        )
        if admin_role is None:
            raise RuntimeError(
                "RBAC admin role is missing. Run migrations first."
            )

        user = await session.scalar(
            select(User).where(User.username == ROOT_USERNAME)
        )
        if user is None:
            user = User(
                username=ROOT_USERNAME,
                email=ROOT_EMAIL,
                password_hash=hash_password(ROOT_PASSWORD),
                is_active=True,
            )
            session.add(user)
            await session.flush()
        else:
            user.email = ROOT_EMAIL
            user.password_hash = hash_password(ROOT_PASSWORD)
            user.is_active = True
            user.deleted_at = None
            user.version += 1

        binding = await session.scalar(
            select(UserRoleBinding).where(
                UserRoleBinding.user_id == user.id,
                UserRoleBinding.role_id == admin_role.id,
            )
        )
        if binding is None:
            session.add(
                UserRoleBinding(user_id=user.id, role_id=admin_role.id)
            )
            return
        if binding.deleted_at is not None:
            binding.deleted_at = None
            binding.version += 1


if __name__ == "__main__":
    asyncio.run(main())
