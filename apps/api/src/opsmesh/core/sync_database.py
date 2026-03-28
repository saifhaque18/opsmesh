"""
Synchronous database access for RQ worker processes.

Workers run outside the async event loop, so they need
a standard synchronous SQLAlchemy session.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.opsmesh.core.config import settings

# Convert async URL to sync URL
# postgresql+asyncpg://... → postgresql+psycopg2://...
SYNC_DATABASE_URL = settings.database_url.replace(
    "postgresql+asyncpg", "postgresql+psycopg2"
)

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=settings.debug,
    pool_size=5,
    max_overflow=5,
)

SyncSessionFactory = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
)


def get_sync_db() -> Session:
    """Get a synchronous database session."""
    return SyncSessionFactory()
