"""Backward-compatible imports for the shared Kafka client."""

from app.core.kafka_client import close_kafka, init_kafka, producer, publish_event

__all__ = ["producer", "init_kafka", "close_kafka", "publish_event"]
