"""Backward-compatible imports for the shared Redis client."""

from app.core.redis_client import (
    check_and_set_webhook_idempotency,
    close_redis,
    get_click_session,
    init_redis,
    redis_client,
    store_click_session,
)

__all__ = [
    "redis_client",
    "init_redis",
    "close_redis",
    "store_click_session",
    "get_click_session",
    "check_and_set_webhook_idempotency",
]
