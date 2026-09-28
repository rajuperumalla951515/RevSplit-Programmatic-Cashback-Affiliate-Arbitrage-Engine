import json
import logging
from typing import Optional, Dict, Any
from aiokafka import AIOKafkaProducer
from app.config import settings

logger = logging.getLogger(__name__)

producer: Optional[AIOKafkaProducer] = None


async def init_kafka():
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        acks="all",  # Strongest durability guarantee for financial event logs
        max_request_size=1048576,
    )
    try:
        await producer.start()
        logger.info("Kafka Producer started successfully.")
    except Exception as e:
        logger.warning(f"Kafka connection warning (producer will retry on publish): {e}")


async def close_kafka():
    global producer
    if producer:
        await producer.stop()
        logger.info("Kafka Producer stopped.")


async def publish_event(topic: str, key: str, value: Dict[str, Any]):
    """Publishes telemetry or postback payload to Kafka asynchronously."""
    global producer
    if not producer:
        logger.error("Kafka Producer is not initialized. Event skipped.")
        return
    try:
        await producer.send_and_wait(topic, key=key, value=value)
        logger.debug(f"Event published to Kafka topic '{topic}' with key '{key}'")
    except Exception as e:
        logger.error(f"Failed to publish event to Kafka topic '{topic}': {e}")
        raise e
