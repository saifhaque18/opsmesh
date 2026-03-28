"""
Create demo users for development.
Run: python -m scripts.seed_admin
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.opsmesh.core.config import settings
from src.opsmesh.models.user import User, UserRole
from src.opsmesh.services.auth_service import hash_password


async def seed():
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession)

    async with session_factory() as session:
        # Check if admin exists
        result = await session.execute(
            select(User).where(User.email == "admin@opsmesh.dev")
        )
        if result.scalar_one_or_none():
            print("Demo users already exist.")
            await engine.dispose()
            return

        admin = User(
            email="admin@opsmesh.dev",
            name="Admin",
            hashed_password=hash_password("opsmesh-admin-2025"),
            role=UserRole.ADMIN,
        )
        session.add(admin)

        analyst = User(
            email="analyst@opsmesh.dev",
            name="Analyst",
            hashed_password=hash_password("opsmesh-analyst-2025"),
            role=UserRole.ANALYST,
        )
        session.add(analyst)

        viewer = User(
            email="viewer@opsmesh.dev",
            name="Viewer",
            hashed_password=hash_password("opsmesh-viewer-2025"),
            role=UserRole.VIEWER,
        )
        session.add(viewer)

        await session.commit()
        print("Created users:")
        print("  admin@opsmesh.dev / opsmesh-admin-2025")
        print("  analyst@opsmesh.dev / opsmesh-analyst-2025")
        print("  viewer@opsmesh.dev / opsmesh-viewer-2025")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
