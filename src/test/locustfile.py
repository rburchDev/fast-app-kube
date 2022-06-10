from locust import FastHttpUser, task, between
from random import randrange


class RabbitUser(FastHttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        with self.client.get(url="/", catch_response=True) as response:
            if response.json()["Status"] != 200:
                response.failure(
                    f"Got Incorrect status code {response.json()['Status']}"
                )
            elif response.json()["Message"] != "Welcome":
                response.failure(
                    f"Got Incorrect message body {response.json()['Message']}"
                )

    @task(5)
    def basic(self):
        num = randrange(start=0, stop=100, step=1)
        with self.client.post(
            url="/v1/info", json={"msg": "LOCUST TEST", "num": num}, catch_response=True
        ) as response:
            if response.json()["Status"] != 200:
                response.failure(
                    f"Got Incorrect status code {response.json()['Status']}"
                )
            elif response.json()["Message"] != "LOCUST TEST":
                response.failure(
                    f"Got Incorrect message body {response.json()['Message']}"
                )
            elif response.json()["Number"] != num:
                response.failure(f"Got Incorrect number {response.json()['Number']}")

    @task
    def rpc(self):
        num = randrange(start=0, stop=10000, step=1)
        with self.client.post(
            url="/v1/v1/random-number", json={"n": num}, catch_response=True
        ) as response:
            if response.json()["Status"] != 200:
                response.failure(
                    f"Got Incorrect status code {response.json()['Status']}"
                )
            elif response.json()["Message"] != f"Random Number Sent {num}":
                response.failure(
                    f"Got Incorrect message body {response.json()['Message']}"
                )
