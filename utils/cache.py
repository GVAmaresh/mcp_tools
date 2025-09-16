
import redis.asyncio as redis
import json
from functools import wraps 
from config import settings
from utils.logger import log
import hashlib

redis_pool = redis.ConnectionPool.from_url(str(settings.REDIS_URL), decode_responses=True)

def get_redis_client():
    return redis.Redis(connection_pool=redis_pool)

async def close_redis():
    await redis_pool.disconnect()

def cached_tool(ttl: int = 300):
    def decorator(func):
        @wraps(func) 
        async def wrapper(*args, **kwargs):
            redis_client = get_redis_client()
            key_parts = {
                "args": [repr(a) for a in args], 
                "kwargs": kwargs
            }
            raw_key = json.dumps(key_parts, sort_keys=True)
            hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
            cache_key = f"{func.__name__}:{hashed_key}"

            try:
                cached_result = await redis_client.get(cache_key)
                if cached_result:
                    log.debug(f"Cache HIT for key: {cache_key}")
                    return json.loads(cached_result)
                log.debug(f"Cache MISS for key: {cache_key}")
            except Exception as e:
                log.error(f"Redis cache error (get): {e}", exc_info=True)

            result = await func(*args, **kwargs)

            try:
                serialized_result = json.dumps(result)
                await redis_client.set(cache_key, serialized_result, ex=ttl)
            except TypeError as e:
                log.error(f"Failed to serialize result for caching: {e}", exc_info=True)
            except Exception as e:
                log.error(f"Redis cache error (set): {e}", exc_info=True)

            return result
        return wrapper
    return decorator





async def test_cache():
    client = get_redis_client()
    await client.set("ping", "pong", ex=10)
    val = await client.get("ping")
    print("Redis test:", val) 
    return { "ping": val}