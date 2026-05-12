"""Seed or reset the local development root user."""

import asyncio

from sqlalchemy import select

from app.auth.model import User
from app.auth.password import hash_password
from app.core.database import session_scope

ROOT_USERNAME = "root"
ROOT_EMAIL = "root@hify.local"
ROOT_PASSWORD = "123456"


async def main() -> None:
    """Create or reset the local root administrator account."""
    async with session_scope(commit_on_exit=True) as session:
        user = await session.scalar(
            select(User).where(User.username == ROOT_USERNAME)
        )
        if user is None:
            session.add(
                User(
                    username=ROOT_USERNAME,
                    email=ROOT_EMAIL,
                    password_hash=hash_password(ROOT_PASSWORD),
                    role="admin",
                    is_active=True,
                )
            )
            return

        user.email = ROOT_EMAIL
        user.password_hash = hash_password(ROOT_PASSWORD)
        user.role = "admin"
        user.is_active = True
        user.deleted_at = None
        user.version += 1


if __name__ == "__main__":
    asyncio.run(main())
