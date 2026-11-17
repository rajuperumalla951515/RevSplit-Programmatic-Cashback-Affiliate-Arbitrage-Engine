import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)
redis_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    global redis_client
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=2.0,
    )
    try:
        await redis_client.ping()
        logger.info("Connected to Redis successfully.")
    except Exception as exc:
        logger.warning("Redis unavailable; cache fallback enabled: %s", exc)


async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None


async def store_click_session(
    sub_id: str,
    click_data: dict[str, Any],
    ttl_seconds: int = settings.CLICK_TOKEN_TTL_SECONDS,
) -> bool:
    if not redis_client:
        return False
    try:
        return bool(await redis_client.set(f"sub_id:{sub_id}", json.dumps(click_data), ex=ttl_seconds))
    except Exception:
        logger.exception("Failed to store click session in Redis.")
        return False


async def get_click_session(sub_id: str) -> Optional[dict[str, Any]]:
    if not redis_client:
        return None
    try:
        data = await redis_client.get(f"sub_id:{sub_id}")
        return json.loads(data) if data else None
    except Exception:
        logger.exception("Failed to read click session from Redis.")
        return None


async def check_and_set_webhook_idempotency(
    merchant_id: str,
    merchant_tx_id: str,
    ttl_seconds: int = 86400,
) -> bool:
    if not redis_client:
        return True
    try:
        key = f"idempotency:{merchant_id}:{merchant_tx_id}"
        return bool(await redis_client.set(key, "PROCESSING", nx=True, ex=ttl_seconds))
    except Exception:
        logger.exception("Redis idempotency check failed.")
        return True
