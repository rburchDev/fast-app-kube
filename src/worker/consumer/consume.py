import asyncio
from threading import Thread
from src.services.rabbitmq.rabb_conn import Broker
from src.logger import StartLog
from src.services.kafka.kafka_conn import KafkaConsumer

rabbitmq = Broker()
log = StartLog()
rootlogger = log.start_logging()
kafka = KafkaConsumer()


async def consumer() -> dict:
    rootlogger.info("Starting Consumer...")
    consume_ok = await rabbitmq.consume(no_ack=False)
    rootlogger.info(consume_ok)
    return {"Status": 200, "Message": "Consumer ran successfully"}


async def rpc_consumer() -> dict:
    rootlogger.info("Starting RPC Consumer")
    consume_ok = await rabbitmq.rpc_consume()
    rootlogger.info(consume_ok)
    return {"Status": 200, "Message": "RPC Consumer ran successfully"}


def kafka_consumer() -> dict:
    rootlogger.info("Starting Kafka Consumer")
    kafka.consumer()
    return {"Status": 200, "Message": "Kafka Consumer ran Successfully"}


if __name__ == "__main__":
    try:
        t1 = Thread(target=kafka_consumer, daemon=True)
        t1.start()
        loop = asyncio.get_event_loop()
        loop.create_task(consumer())
        loop.create_task(rpc_consumer())
        loop.run_forever()
    except:
        rootlogger.error("ERROR")
