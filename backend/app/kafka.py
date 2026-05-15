from aiokafka import AIOKafkaProducer

from app.config import settings

producer: AIOKafkaProducer | None = None


async def init_kafka():
    global producer
    producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
    await producer.start()


async def close_kafka():
    global producer
    if producer:
        await producer.stop()
        producer = None


async def send_event(topic: str, key: bytes, value: bytes):
    assert producer is not None
    await producer.send_and_wait(topic, key=key, value=value)
