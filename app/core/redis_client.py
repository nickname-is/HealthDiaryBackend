from redis.asyncio import Redis, from_url

from app.core.config import settings

redis_client: Redis = from_url(settings.redis.url, decode_responses=True)


async def close_redis() -> None:
    await redis_client.aclose()
