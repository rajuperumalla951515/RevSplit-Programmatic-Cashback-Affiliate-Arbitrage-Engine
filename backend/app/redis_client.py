import json
import logging
from typing import Optional, Dict, Any
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)

redis_client: Optional[redis.Redis] = None


async def init_redis():
    global redis_client
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        decode_responses=True,
    )
    logger.info("Connected to Redis server successfully.")


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed.")


async def store_click_session(sub_id: str, click_data: Dict[str, Any], ttl_seconds: int = settings.CLICK_TOKEN_TTL_SECONDS) -> bool:
    """Stores click token mapping in Redis for high-speed sub_id retrieval."""
    if not redis_client:
        raise RuntimeError("Redis client is not initialized")
    key = f"sub_id:{sub_id}"
    return await redis_client.set(key, json.dumps(click_data), ex=ttl_seconds)


async def get_click_session(sub_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves click token mapping from Redis."""
    if not redis_client:
        raise RuntimeError("Redis client is not initialized")
    key = f"sub_id:{sub_id}"
    data = await redis_client.get(key)
    return json.loads(data) if data else None


async def check_and_set_webhook_idempotency(merchant_id: str, merchant_tx_id: str, ttl_seconds: int = 86400) -> bool:
    """Atomic SETNX in Redis to deduplicate rapid webhook retries."""
    if not redis_client:
        raise RuntimeError("Redis client is not initialized")
    key = f"webhook_idempotency:{merchant_id}:{merchant_tx_id}"
    # SETNX: returns True if key was set (first time seen), False if already exists
    return await redis_client.set(key, "PROCESSED", ex=ttl_seconds, nx=True)
