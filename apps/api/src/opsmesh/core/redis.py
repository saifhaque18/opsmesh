import redis as sync_redis
import redis.asyncio as aioredis

from src.opsmesh.core.config import settings


def get_sync_redis() -> sync_redis.Redis:
    """Synchronous Redis client for RQ workers."""
    return sync_redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )


async def get_async_redis() -> aioredis.Redis:
    """Async Redis client for the API layer."""
    return aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
    )


async def check_redis_health() -> bool:
    """Check if Redis is reachable."""
    try:
        client = await get_async_redis()
        await client.ping()
        await client.aclose()
        return True
    except Exception:
        return False
