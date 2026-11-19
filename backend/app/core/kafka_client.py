import json
import logging
import socket
from typing import Any, Optional

from aiokafka import AIOKafkaProducer

from app.core.config import settings

logger = logging.getLogger(__name__)
producer: Optional[AIOKafkaProducer] = None


def _is_kafka_reachable(bootstrap_servers: str, timeout: float = 0.2) -> bool:
    try:
        host, port_str = bootstrap_servers.split(":", 1)
        with socket.create_connection((host, int(port_str)), timeout=timeout):
            return True
    except Exception:
        return False


async def init_kafka() -> None:
    global producer
    if not _is_kafka_reachable(settings.KAFKA_BOOTSTRAP_SERVERS):
        producer = None
        logger.info("Kafka broker not reachable at %s; telemetry fallback enabled.", settings.KAFKA_BOOTSTRAP_SERVERS)
        return

    try:
        p = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            key_serializer=lambda key: key.encode("utf-8") if key else None,
            acks="all",
            max_request_size=1048576,
            request_timeout_ms=1000,
        )
        await p.start()
        producer = p
        logger.info("Kafka producer started successfully.")
    except Exception as exc:
        producer = None
        logger.warning("Kafka broker connection failed (%s); continuing in fallback mode.", exc)


async def close_kafka() -> None:
    global producer
    if producer:
        try:
            await producer.stop()
        except Exception:
            pass
        producer = None
        logger.info("Kafka producer stopped.")


async def publish_event(topic: str, key: str, value: dict[str, Any]) -> None:
    if not producer:
        logger.debug("Kafka producer not active; event for topic '%s' skipped (in-memory mode).", topic)
        return
    try:
        await producer.send_and_wait(topic, key=key, value=value)
    except Exception:
        logger.warning("Failed to publish event to Kafka topic '%s'; continuing in degraded mode.", topic)
