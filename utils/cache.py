# utils/cache.py
import redis.asyncio as redis
import json
from functools import wraps
from config import settings
from utils.logger import log

# Create a single, shared Redis connection pool
redis_pool = redis.ConnectionPool.from_url(settings.redis_url, decode_responses=True)

def get_redis_client():
    return redis.Redis(connection_pool=redis_pool)

def cached_tool(ttl: int = 3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key_parts = [func.__name__] + [str(a) for a in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
            cache_key = ":".join(key_parts)

            redis_client = get_redis_client()
            try:
                cached_result = await redis_client.get(cache_key)
                if cached_result:
                    log.info(f"CACHE HIT for tool '{func.__name__}' with key '{cache_key}'")
                    return json.loads(cached_result) 
            except Exception as e:
                log.error(f"Redis GET failed for key '{cache_key}': {e}")


            log.info(f"CACHE MISS for tool '{func.__name__}' with key '{cache_key}'")
            result = await func(*args, **kwargs)

            try:
                await redis_client.set(cache_key, json.dumps(result), ex=ttl)
            except Exception as e:
                log.error(f"Redis SET failed for key '{cache_key}': {e}")


            return result
        return wrapper
    return decorator