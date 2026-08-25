import json
from redis.asyncio import Redis
from app.core.config import settings


class JsonCache:
    def __init__(self, url: str, prefix: str):
        self.redis = Redis.from_url(url, decode_responses=True)
        self.prefix = prefix

    async def get(self, key):
        value = await self.redis.get(f"{self.prefix}:{key}")
        return json.loads(value) if value else None

    async def set(self, key, value, ttl):
        await self.redis.setex(f"{self.prefix}:{key}", ttl, json.dumps(value, default=str))

    async def add(self, key, value, ttl) -> bool:
        """Set only when absent (NX) — used for short-lived locks. False if held."""
        return bool(await self.redis.set(f"{self.prefix}:{key}", json.dumps(value, default=str), ex=ttl, nx=True))

    async def delete(self, key):
        await self.redis.delete(f"{self.prefix}:{key}")


short_cache = JsonCache(settings.cache_short_url, "docetra:short")
