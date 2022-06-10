import asyncio
import aiormq
import os
import json
import time
from aiormq.abc import AbstractConnection, DeliveredMessage
from aiormq.base import Base
from yarl import URL
from uuid import uuid4
from src.logger import StartLog
from src.services.kafka.kafka_conn import KafkaProducer


class Worker:
    log = StartLog()
    rootlogger = log.start_logging()

    def __init__(
        self, rabbit_server: str, rabbit_port: int, rabbit_un: str, rabbit_pw: str
    ):
        self.rootlogger.info("Starting Worker")
        self.rabbit_server: str = rabbit_server
        self.rabbit_port: int = rabbit_port
        self.rabbit_username: str = rabbit_un
        self.rabbit_password: str = rabbit_pw
        self.loop = asyncio.get_event_loop()

        self.conn = None
        self.channel = None
        self.declare_ok = None
        self.conn_rpc_consume = None
        self.channel_rpc_consume = None
        self.declare_ok_rpc_consume = None
        self.conn_rpc_publish = None
        self.channel_rpc_publish = None
        self.declare_ok_rpc_publish = None
        self.callback_queue = ""

        self.futures = {}

        self.url = URL(
            f"amqp://{self.rabbit_username}:{self.rabbit_password}@{self.rabbit_server}:{self.rabbit_port}/"
        )
        self.data = {
            "Rabbit": self.url,
            "AIORMQ": [
                self.conn,
                self.channel,
                self.declare_ok,
                self.conn_rpc_consume,
                self.channel_rpc_consume,
                self.declare_ok_rpc_consume,
                self.conn_rpc_publish,
                self.channel_rpc_publish,
                self.declare_ok_rpc_publish,
                self.callback_queue,
            ],
        }

        self.kc = KafkaProducer()

        self.rootlogger.debug(f"INIT data for Worker: {self.data}")

    async def on_message(self, message: DeliveredMessage) -> None:
        self.rootlogger.info(f"Received message: {message.body.decode()}")
        if message.routing_key == "rabbit":
            self.rootlogger.debug("Received message with rabbit routing key...")
        elif message.routing_key == "kafka":
            self.rootlogger.debug("Received message with kafka routing key...")
            kc_json = json.loads(message.body.decode())
            self.kc.producer(message=kc_json)
        await message.channel.basic_ack(message.delivery_tag)

    async def rpc_on_message(self, message: DeliveredMessage) -> None:
        n = int(message.body.decode())

        self.rootlogger.info(f"Received RPC message {n}")

        await message.channel.basic_publish(
            body=str(n).encode(),
            routing_key=message.header.properties.reply_to,
            properties=aiormq.spec.Basic.Properties(
                correlation_id=message.header.properties.correlation_id
            ),
        )

        await message.channel.basic_ack(message.delivery_tag)
        self.rootlogger.info("RPC Request Complete")

    async def on_response(self, message: DeliveredMessage):
        self.rootlogger.info(f"Message from ROC: {message.body.decode()}")
        future = self.futures.pop(message.header.properties.correlation_id)
        future.set_result(message.body)
        await message.channel.basic_ack(message.delivery_tag)

    async def start_connections(self) -> AbstractConnection:
        conn_data = {
            "rabbit_server": self.rabbit_server,
            "rabbit_port": self.rabbit_port,
            "rabbit_username": self.rabbit_username,
            "rabbit_password": self.rabbit_password,
        }
        self.rootlogger.info(f"Rabbit Connection {conn_data}")
        return await aiormq.connect(url=self.url)

    async def start_channel(self) -> tuple:
        self.rootlogger.info(
            f"Connection: {self.conn} Channel: {self.channel} BaseClosed: {Base.is_closed}"
        )
        if self.conn is None or Base.is_closed:
            self.conn = await self.start_connections()
            self.channel = await self.conn.channel()
            await self.channel.basic_qos(prefetch_count=1)

            await self.channel.exchange_declare(exchange="api", exchange_type="fanout")

            self.declare_ok = await self.channel.queue_declare(
                queue="rabbit", exclusive=False, auto_delete=True
            )
            await self.channel.queue_bind(queue=self.declare_ok.queue, exchange="api")
        return self.channel, self.declare_ok

    async def start_channel_rpc_consume(self) -> aiormq:
        if self.conn_rpc_consume is None or Base.is_closed:
            self.conn_rpc_consume = await self.start_connections()
            self.channel_rpc_consume = await self.conn_rpc_consume.channel()

            self.declare_ok_rpc_consume = await self.channel_rpc_consume.queue_declare(
                queue="rpc_queue"
            )

        return self.declare_ok_rpc_consume

    async def start_channel_rpc_publish(self) -> tuple:
        if self.conn_rpc_publish is None or Base.is_closed:
            self.conn_rpc_publish = await self.start_connections()
            self.channel_rpc_publish = await self.conn_rpc_publish.channel()

            self.declare_ok_rpc_publish = await self.channel_rpc_publish.queue_declare(
                queue="rpc_reply_queue", exclusive=False, auto_delete=True
            )

            self.callback_queue = self.declare_ok_rpc_publish.queue

            return self.channel_rpc_publish, self.declare_ok_rpc_publish


class Broker(Worker):
    def __init__(self):
        self.rootlogger.info("Starting Broker")
        super().__init__(
            rabbit_server=os.environ["MY_POD_NAME"],
            rabbit_port=5672,
            rabbit_un=os.environ["RABBIT_USERNAME"],
            rabbit_pw=os.environ["RABBIT_PASSWORD"],
        )

    async def send_message(self, body: bytes, routing_key: str, exchange: str) -> None:
        try:
            await self.start_channel()
            await self.channel.basic_publish(
                body=body, routing_key=routing_key, exchange=exchange
            )
        except aiormq.exceptions.ChannelInvalidStateError as c:
            self.conn = None
            self.rootlogger.error(f"Error with channel {c}")
            await self.start_channel()
            await self.channel.basic_publish(
                body=body, routing_key=routing_key, exchange=exchange
            )

    async def consume(self, no_ack: bool = False) -> None:
        try:
            await self.start_channel()
            consume_ok = await self.channel.basic_consume(
                queue=self.declare_ok.queue,
                no_ack=no_ack,
                consumer_callback=self.on_message,
            )
        except aiormq.exceptions.ChannelInvalidStateError as e:
            self.conn = None
            self.rootlogger.error(f"Error with channel {e}")
            await self.start_channel()
            consume_ok = await self.channel.basic_consume(
                queue=self.declare_ok.queue,
                no_ack=no_ack,
                consumer_callback=self.on_message,
            )
        except ConnectionError as ce:
            self.rootlogger.warning(
                f"Connection Error: {ce}... Waiting 10 seconds and trying again..."
            )
            time.sleep(10)
            try:
                await self.start_channel()
                consume_ok = await self.channel.basic_consume(
                    queue=self.declare_ok.queue,
                    no_ack=no_ack,
                    consumer_callback=self.on_message,
                )
            except ConnectionError as ce2:
                self.rootlogger.warning(
                    f"Connection Error: {ce2}... Waiting 20 seconds and trying again..."
                )
                time.sleep(20)
                await self.start_channel()
                consume_ok = await self.channel.basic_consume(
                    queue=self.declare_ok.queue,
                    no_ack=no_ack,
                    consumer_callback=self.on_message,
                )
        self.rootlogger.debug(consume_ok)

    async def rpc_consume(self) -> None:
        try:
            await self.start_channel_rpc_consume()
            await self.channel_rpc_consume.basic_consume(
                queue=self.declare_ok_rpc_consume.queue,
                consumer_callback=self.rpc_on_message,
            )
        except aiormq.exceptions.ChannelInvalidStateError as e:
            self.conn_rpc_consume = None
            self.rootlogger.error(f"Error with channel {e}")
            await self.start_channel_rpc_consume()
            await self.channel_rpc_consume.basic_consume(
                queue=self.declare_ok_rpc_consume.queue,
                consumer_callback=self.rpc_on_message,
            )
        except ConnectionError as ce:
            self.rootlogger.warning(
                f"Connection Error: {ce}... Waiting 10 seconds and trying again..."
            )
            time.sleep(10)
            try:
                await self.start_channel_rpc_consume()
                await self.channel_rpc_consume.basic_consume(
                    queue=self.declare_ok_rpc_consume.queue,
                    consumer_callback=self.rpc_on_message,
                )
            except ConnectionError as ce2:
                self.rootlogger.warning(
                    f"Connection Error: {ce2}... Waiting 20 seconds and trying again..."
                )
                time.sleep(20)
                await self.start_channel_rpc_consume()
                await self.channel_rpc_consume.basic_consume(
                    queue=self.declare_ok_rpc_consume.queue,
                    consumer_callback=self.rpc_on_message,
                )

    async def rpc_reply_consume(self) -> None:
        try:
            await self.start_channel_rpc_publish()
            await self.channel_rpc_publish.basic_consume(
                queue="rpc_reply_queue", consumer_callback=self.on_response
            )
        except aiormq.exceptions.ChannelInvalidStateError as e:
            self.conn_rpc_publish = None
            self.rootlogger.error(f"Error with channel {e}")
            await self.start_channel_rpc_publish()
            await self.channel_rpc_publish.basic_consume(
                queue="rpc_reply_queue", consumer_callback=self.on_response
            )

    async def rpc_send_message(self, n: int, loop: asyncio.get_event_loop) -> int:
        self.rootlogger.info("Starting RPC Send Message")
        correlation_id = str(uuid4())
        future = loop.create_future()

        self.futures[correlation_id] = future
        self.rootlogger.debug(f"Future setup {self.futures}, FUTURE: {future}")
        try:
            await self.start_channel_rpc_publish()
            self.rootlogger.info("Starting Channel")
            await self.channel_rpc_publish.basic_publish(
                body=str(n).encode(),
                routing_key="rpc_queue",
                properties=aiormq.spec.Basic.Properties(
                    content_type="text/plain",
                    correlation_id=correlation_id,
                    reply_to=self.callback_queue,
                ),
            )
        except aiormq.exceptions.ChannelInvalidStateError as e:
            self.conn_rpc_publish = None
            self.rootlogger.error(f"Error with channel {e}")
            await self.start_channel_rpc_publish()
            self.rootlogger.info("Starting Channel")
            await self.channel_rpc_publish.basic_publish(
                body=str(n).encode(),
                routing_key="rpc_queue",
                properties=aiormq.spec.Basic.Properties(
                    content_type="text/plain",
                    correlation_id=correlation_id,
                    reply_to=self.callback_queue,
                ),
            )
        self.rootlogger.info("Message published")
        await self.rpc_reply_consume()
        self.rootlogger.debug(f"Message {int(await future)}")
        return int(await future)
