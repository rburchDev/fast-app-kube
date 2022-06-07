import asyncio
from app.services.rabbitmq.rabb_conn import Broker
from app.logger import Log

rabbitmq = Broker()
log = Log(name="Consume")
rootlogger = log.logging()


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


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(consumer())
        loop.create_task(rpc_consumer())
        loop.run_forever()
    except:
        rootlogger.error("ERROR")