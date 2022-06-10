import os
import json
from dataclasses_avroschema import AvroModel
from abc import ABC
from confluent_kafka import avro, KafkaError
from confluent_kafka.avro import AvroProducer, AvroConsumer
from confluent_kafka.avro.serializer import SerializerError
from src.logger import StartLog


class Computer(AvroModel):
    """Computer Key"""
    computer_name: str

    class Meta:
        namespace = "Computer.v1"


class System(AvroModel):
    """Computer Information"""
    system: str
    release: str
    version: str
    machine: str
    processor: str

    class Meta:
        namespace = "Computer.v1"


class CreateSchema(ABC):
    """Class to Create Schema for Kafka"""
    log = StartLog()
    rootlogger = log.start_logging()

    def __init__(self, system: System(), computer: Computer()):
        self.rootlogger.info("Starting CreateSchema for Kafka service...")
        self.system = system
        self.computer = computer

        self.base_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
        self.key_schema = os.path.join(self.base_path, "KeySchema.avsc")
        self.value_schema = os.path.join(self.base_path, "ValueSchema.avsc")

        self.ks_json = None
        self.vs_json = None

    def create_schema_file(self) -> None:
        self.rootlogger.info("Checking Kafka Schema")
        if os.path.isfile(self.key_schema):
            self.rootlogger.debug(f"File Found: {self.key_schema}")
        else:
            self.rootlogger.debug(f"File not found, creating {self.key_schema}...")
            with open(self.key_schema, "w+", encoding='utf-8') as ks:
                self.ks_json = self.computer.avro_schema_to_python()
                json.dump(obj=self.ks_json, fp=ks, ensure_ascii=False, indent=4)
        if os.path.isfile(self.value_schema):
            self.rootlogger.debug(f"File Found: {self.value_schema}")
        else:
            self.rootlogger.debug(f"File not found, creating {self.value_schema}...")
            with open(self.value_schema, "w+", encoding='utf-8') as vs:
                self.vs_json = self.system.avro_schema_to_python()
                json.dump(obj=self.vs_json, fp=vs, ensure_ascii=False, indent=4)


class KafkaProducer(CreateSchema):
    """Class to Set Up a Producer for Kafka"""
    def __init__(self):
        super().__init__(computer=Computer, system=System)
        self.rootlogger.info("Starting Kafka Producer Class...")
        self.create_schema_file()
        self.load_key_schema = avro.load(self.key_schema)
        self.load_value_schema = avro.load(self.value_schema)

        self.key: dict = {}
        self.value: dict = {}

        self.avor_producer: AvroProducer = AvroProducer(
            {'bootstrap.servers': 'PLAINTEXT://kafka01.daas.charterlab.com:9092',
             'schema.registry.url': 'http://kafka01.daas.charterlab.com:8081',
             'receive.message.max.bytes': '15000000000',
             'security.protocol': 'PLAINTEXT'},
            default_key_schema=self.load_key_schema, default_value_schema=self.load_value_schema
        )

        self.msg: str = ""
        self.status: int = 0

    def callback(self, err: str, msg) -> dict:
        if err is not None:
            self.msg = f"FAILED to deliver message: {err}"
            self.status = 500
            self.rootlogger.error(f"Status: {self.status} with {self.msg}")
        else:
            self.msg = f"Produced to: {msg.topic()} [{msg.partition()}] @ {msg.offset()}"
            self.status = 200
            self.rootlogger.info(f"Status: {self.status} with {self.msg}")
        return {"Status": self.status, "Message": self.msg}

    def producer(self, message: dict) -> dict:
        self.rootlogger.info("Starting Producer function")
        for key, value in message.items():
            self.key = {"computer_name": key}
            self.value = value
            self.rootlogger.debug(f"Key: {self.key}, Value: {self.value}")
        self.avor_producer.produce(topic='ryan_burch', value=self.value, key=self.key,
                                   key_schema=self.load_key_schema, value_schema=self.load_value_schema,
                                   callback=self.callback)
        self.avor_producer.poll(10)
        self.rootlogger.debug("Message was sent succesfully")
        return {"Status": 200, "Message": "Successfully sent Message to Kafka"}


class KafkaConsumer(CreateSchema):
    """Class to Set Up a Consumer for Kafka"""
    def __init__(self):
        super().__init__(computer=Computer, system=System)
        self.running: bool = True

        self.avro_consumer: AvroConsumer = AvroConsumer(
            {'bootstrap.servers': 'PLAINTEXT://kafka01.daas.charterlab.com:9092',
             'schema.registry.url': 'http://kafka01.daas.charterlab.com:8081',
             'receive.message.max.bytes': '15000000000',
             'security.protocol': 'PLAINTEXT',
             'api.version.request': True,
             'group.id': 'ryan_burch-1'}
        )

        self.msg: AvroConsumer.poll = None
        self.return_message: dict = {}

    def consumer(self):
        self.avro_consumer.subscribe(['ryan_burch'])
        while self.running:
            try:
                self.msg = self.avro_consumer.poll(10)
                if self.msg:
                    if not self.msg.error():
                        value_json = json.dumps(self.msg.value())
                        vj = json.loads(value_json)
                        self.return_message[self.msg.key()["computer_name"]] = vj
                        self.return_message[self.msg.key()["computer_name"]].\
                            update({"Partition": str(self.msg.partition())})
                        self.return_message[self.msg.key()["computer_name"]].update({"Offset": str(self.msg.offset())})
                        self.rootlogger.info(f"Consumed Message: {self.return_message}")
                        self.avro_consumer.commit()
                    elif self.msg.error().code() != KafkaError._PARTITION_EOF:
                        self.rootlogger.error(f"Error with Kafka: {self.msg.error()}")
                else:
                    self.rootlogger.debug("No Message in Kafka... Trying again....")
            except SerializerError as se:
                self.rootlogger.error(f"Message deserialization error for {self.msg}: {se}")
                self.running = False
        self.avro_consumer.commit()
        self.avro_consumer.close()


if __name__ == "__main__":
    kc = KafkaConsumer()
    kc.consumer()
