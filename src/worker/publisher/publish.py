import asyncio
import platform
import json
import subprocess
from random import randrange
from pydantic import BaseModel
from fastapi import APIRouter
from src.services.rabbitmq.rabb_conn import Broker
from src.logger import StartLog


app_route = APIRouter()
rabbitmq = Broker()
log = StartLog()
rootlogger = log.start_logging()


class Item(BaseModel):
    msg: str = None
    num: int = None


class Number(BaseModel):
    n: int = randrange(1, 1000000000, 1)


class Kafka(BaseModel):
    computer_name: str = platform.node()
    system: str = platform.system()
    release: str = platform.release()
    version: str = platform.version()
    machine: str = platform.machine()
    processor: str = None


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


@app_route.post("/kafka")
async def kafka_message(kafka: Kafka) -> dict:
    rootlogger.info("Starting kafka message")
    loop = asyncio.get_event_loop()
    loop.create_task(kafka_publish(kafka=kafka))
    rootlogger.info("POST received from API")
    return {"Status": 200, "Message": f"Sent Message with {kafka}"}


async def publish(item: Item) -> None:
    rootlogger.info("Starting Publisher...")
    await rabbitmq.send_message(
        body=f"Message: {item.msg} Number: {item.num}".encode(),
        routing_key="rabbit",
        exchange="api",
    )
    rootlogger.debug("Message Sent...")


async def rpc_publish(number: Number, loop: asyncio.get_event_loop) -> None:
    rootlogger.info("Starting RPC Publisher...")
    await rabbitmq.rpc_send_message(n=number.n, loop=loop)
    rootlogger.info("RPC Message Sent....")


async def kafka_publish(kafka: Kafka) -> None:
    rootlogger.info("Starting Publisher...")
    if kafka.system == "Linux":
        command = 'cat /proc/cpuinfo | grep "model name" | head -1 | cut -d : -f 2'
        kafka.processor = (
            subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            .communicate()[0]
            .decode()
            .strip()
        )
    elif kafka.system == "Windows":
        kafka.processor = platform.processor()
    else:
        kafka.processor = (
            subprocess.Popen(
                ["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"],
                stdout=subprocess.PIPE,
            )
            .communicate()[0]
            .decode()
            .strip()
        )
    message_json = {
        kafka.computer_name: {
            "system": kafka.system,
            "release": kafka.release,
            "version": kafka.version,
            "machine": kafka.machine,
            "processor": kafka.processor,
        }
    }
    message_dump = json.dumps(message_json)
    rootlogger.debug(f"Sending: {message_dump}")
    await rabbitmq.send_message(
        body=message_dump.encode(), routing_key="kafka", exchange="api"
    )
    rootlogger.info("Message Sent...")
