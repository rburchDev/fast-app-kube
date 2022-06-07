import asyncio
from random import randrange
from pydantic import BaseModel
from fastapi import APIRouter
from src.services.rabbitmq.rabb_conn import Broker
from src.logger import Log


app_route = APIRouter()
rabbitmq = Broker()
log = Log(name="Publish")
rootlogger = log.logging()


class Item(BaseModel):
    msg: str = None
    num: int = None


class Number(BaseModel):
    n: int = randrange(1, 1000000000, 1)


@app_route.post("/info")
async def main(item: Item) -> dict:
    rootlogger.info("Starting Main")
    loop = asyncio.get_event_loop()
    loop.create_task(publish(item=item))
    rootlogger.info("POST received from API")
    return {"Status": 200, "Message": item.msg, "Number": item.num}


@app_route.post("/random-number")
async def rand(number: Number) -> dict:
    rootlogger.info("Starting rand")
    loop = asyncio.get_event_loop()
    loop.create_task(rpc_publish(number=number, loop=loop))
    rootlogger.info("POST received from API")
    return {"Status": 200, "Message": f"Random Number Sent {number.n}"}


async def publish(item: Item) -> None:
    rootlogger.info("Starting Publisher...")
    await rabbitmq.send_message(body=f"Message: {item.msg} Number: {item.num}".encode(),
                                routing_key="rabbit",
                                exchange='api')
    rootlogger.debug("Message Sent...")


async def rpc_publish(number: Number, loop: asyncio.get_event_loop) -> None:
    rootlogger.info("Starting RPC Publisher...")
    await rabbitmq.rpc_send_message(n=number.n, loop=loop)
    rootlogger.info("RPC Message Sent....")
