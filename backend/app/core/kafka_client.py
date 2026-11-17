import json
import logging
from typing import Any, Optional

from aiokafka import AIOKafkaProducer

from app.core.config import settings

logger = logging.getLogger(__name__)
producer: Optional[AIOKafkaProducer] = None


async def init_kafka() -> None:
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        key_serializer=lambda key: key.encode("utf-8") if key else None,
        acks="all",
        max_request_size=1048576,
    )
    try:
        await producer.start()
        logger.info("Kafka producer started successfully.")
    except Exception as exc:
        logger.warning("Kafka connection warning: %s", exc)


async def close_kafka() -> None:
    global producer
    if producer:
        await producer.stop()
        producer = None
        logger.info("Kafka producer stopped.")


async def publish_event(topic: str, key: str, value: dict[str, Any]) -> None:
    if not producer:
        logger.error("Kafka producer is not initialized; event skipped.")
        return
    try:
        await producer.send_and_wait(topic, key=key, value=value)
    except Exception:
        logger.exception("Failed to publish event to Kafka topic '%s'.", topic)
        raise
