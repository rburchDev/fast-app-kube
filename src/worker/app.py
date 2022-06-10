import uvicorn
import time
from src.worker.publisher.publish import app_route
from fastapi import FastAPI
from src.services.rabbitmq.rabb_conn import Broker
from src.logger import StartLog

app = FastAPI()


class RyanApp:
    log = StartLog()
    rootlogger = log.start_logging()

    def __init__(self, rabbit_conn: Broker):
        app.include_router(app_route, prefix="/v1")
        self.uv_server = uvicorn.Server(
            uvicorn.Config(
                app=app,
                host="0.0.0.0",
                port=3000,
                log_level='debug'
            )
        )
        self.rabbit_conn = rabbit_conn

        @app.on_event("startup")
        async def startup_event() -> tuple:
            try:
                channel = await self.rabbit_conn.start_channel()
            except ConnectionError as ce:
                self.rootlogger.warn(f"Connection Error: {ce}... Waiting 10 seconds and trying again...")
                time.sleep(10)
                try:
                    channel = await self.rabbit_conn.start_channel()
                except ConnectionError as ce2:
                    self.rootlogger.warn(f"Connection Error: {ce2}... Waiting 20 seconds and trying again...")
                    time.sleep(20)
                    channel = await self.rabbit_conn.start_channel()
            return channel

        @app.get("/")
        def index() -> dict:
            return {"Status": 200, "Message": "Welcome"}


if __name__ == "__main__":
    rabbitmq = Broker()
    api = RyanApp(rabbit_conn=rabbitmq)
    api.uv_server.run()
