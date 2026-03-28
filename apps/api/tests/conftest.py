"""
Shared test fixtures for the OpsMesh test suite.

Architecture:
- Uses a real PostgreSQL test database (opsmesh_test)
- Each test gets a fresh database state (truncated tables at start)
- Factory functions create realistic test data
- Auth fixtures provide pre-authenticated users and tokens
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.opsmesh.core.config import settings
from src.opsmesh.core.database import get_db
from src.opsmesh.main import app
from src.opsmesh.models.base import Base
from src.opsmesh.models.user import User, UserRole
from src.opsmesh.services.auth_service import create_access_token, hash_password

# ─── Test database URL ─────────────────────────────
if "opsmesh_test" in settings.database_url:
    TEST_DATABASE_URL = settings.database_url
else:
    import re

    TEST_DATABASE_URL = re.sub(r"/([^/]+)$", "/opsmesh_test", settings.database_url)


# ─── Engine for tests ──────────────────────────────
@pytest_asyncio.fixture
async def test_engine():
    """
    Create a test engine and set up tables.

    Truncates all tables at the START of each test to ensure clean state.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        # Create all tables (idempotent - won't fail if they exist)
        await conn.run_sync(Base.metadata.create_all)

        # Delete all data at the START of the test to ensure clean state
        # Using DELETE instead of TRUNCATE to avoid exclusive locks
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"DELETE FROM {table.name}"))

    yield engine

    # No cleanup at end - truncation happens at start of next test
    await engine.dispose()


# ─── Database session per test ─────────────────────
@pytest_asyncio.fixture
async def db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for each test."""
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        yield session
        # Commit any pending changes (factories create data)
        await session.commit()


# ─── Override the FastAPI database dependency ──────
@pytest_asyncio.fixture
async def client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for testing API endpoints.

    Creates a new session for each request to avoid connection conflicts.
    """
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ─── Factory functions ─────────────────────────────


@pytest_asyncio.fixture
async def user_factory(db: AsyncSession):
    """Factory for creating test users."""

    async def _create(
        email: str | None = None,
        name: str = "Test User",
        password: str = "test-password-123",
        role: UserRole = UserRole.ANALYST,
    ) -> User:
        user = User(
            email=email or f"test-{uuid.uuid4().hex[:8]}@opsmesh.dev",
            name=name,
            hashed_password=hash_password(password),
            role=role,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    return _create


@pytest_asyncio.fixture
async def admin_user(user_factory) -> User:
    """Pre-created admin user."""
    return await user_factory(
        email="admin@test.com", name="Admin", role=UserRole.ADMIN
    )


@pytest_asyncio.fixture
async def analyst_user(user_factory) -> User:
    """Pre-created analyst user."""
    return await user_factory(
        email="analyst@test.com", name="Analyst", role=UserRole.ANALYST
    )


@pytest_asyncio.fixture
async def viewer_user(user_factory) -> User:
    """Pre-created viewer user."""
    return await user_factory(
        email="viewer@test.com", name="Viewer", role=UserRole.VIEWER
    )


def make_auth_header(user: User) -> dict:
    """Create an Authorization header for a test user."""
    token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role.value,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def incident_factory(db: AsyncSession):
    """Factory for creating test incidents."""
    from src.opsmesh.models.incident import (
        Incident,
        IncidentSeverity,
        IncidentStatus,
    )

    async def _create(
        title: str = "Test incident",
        source: str = "test",
        severity: IncidentSeverity = IncidentSeverity.MEDIUM,
        status: IncidentStatus = IncidentStatus.OPEN,
        service: str | None = "test-service",
        environment: str | None = "prod",
        **kwargs,
    ) -> Incident:
        incident = Incident(
            title=title,
            source=source,
            severity=severity,
            status=status,
            service=service,
            environment=environment,
            detected_at=datetime.now(UTC),
            processing_status="pending",
            **kwargs,
        )
        db.add(incident)
        await db.flush()
        await db.refresh(incident)
        return incident

    return _create
