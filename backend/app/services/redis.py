"""
Redis client — real-time alert pub/sub for the dashboard.
"""
import json
import redis.asyncio as aioredis
from app.core.config import settings

_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _pool


async def publish_alert(tenant_slug: str, alert: dict) -> None:
    r = await get_redis()
    channel = f"{settings.REDIS_ALERTS_CHANNEL}:{tenant_slug}"
    await r.publish(channel, json.dumps(alert))


async def subscribe_alerts(tenant_slug: str):
    """Async generator — yields alert dicts as they arrive."""
    r = await get_redis()
    pubsub = r.pubsub()
    channel = f"{settings.REDIS_ALERTS_CHANNEL}:{tenant_slug}"
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield json.loads(message["data"])
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
