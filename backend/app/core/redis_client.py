import json
import logging
import socket
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)
redis_client: Optional[redis.Redis] = None
_memory_cache: dict[str, str] = {}


def _is_redis_reachable(host: str, port: int, timeout: float = 0.2) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


async def init_redis() -> None:
    global redis_client
    if not _is_redis_reachable(settings.REDIS_HOST, settings.REDIS_PORT):
        redis_client = None
        logger.info("Redis server not reachable at %s:%s; using high-speed in-memory cache.", settings.REDIS_HOST, settings.REDIS_PORT)
        return

    try:
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=1.0,
            socket_timeout=1.0,
        )
        await client.ping()
        redis_client = client
        logger.info("Connected to Redis successfully.")
    except Exception as exc:
        redis_client = None
        logger.warning("Redis ping failed (%s); cache fallback enabled.", exc)


async def close_redis() -> None:
    global redis_client
    if redis_client:
        try:
            await redis_client.aclose()
        except Exception:
            pass
        redis_client = None


async def store_click_session(
    sub_id: str,
    click_data: dict[str, Any],
    ttl_seconds: int = settings.CLICK_TOKEN_TTL_SECONDS,
) -> bool:
    key = f"sub_id:{sub_id}"
    _memory_cache[key] = json.dumps(click_data)
    if redis_client:
        try:
            return bool(await redis_client.set(key, json.dumps(click_data), ex=ttl_seconds))
        except Exception:
            return True
    return True


async def get_click_session(sub_id: str) -> Optional[dict[str, Any]]:
    key = f"sub_id:{sub_id}"
    if redis_client:
        try:
            data = await redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception:
            pass

    data = _memory_cache.get(key)
    return json.loads(data) if data else None


async def check_and_set_webhook_idempotency(
    merchant_id: str,
    merchant_tx_id: str,
    ttl_seconds: int = 86400,
) -> bool:
    key = f"idempotency:{merchant_id}:{merchant_tx_id}"
    if key in _memory_cache:
        return False
    _memory_cache[key] = "PROCESSING"

    if redis_client:
        try:
            return bool(await redis_client.set(key, "PROCESSING", nx=True, ex=ttl_seconds))
        except Exception:
            return True
    return True
