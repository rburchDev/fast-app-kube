import uvicorn
from .publisher import app_route
from fastapi import FastAPI
from app.services.rabbitmq.rabb_conn import Broker

app = FastAPI()


class RyanApp:
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
            channel = await self.rabbit_conn.start_channel()
            return channel

        @app.get("/")
        def index() -> dict:
            return {"Status": 200, "Message": "Welcome"}


if __name__ == "__main__":
    rabbitmq = Broker()
    api = RyanApp(rabbit_conn=rabbitmq)
    api.uv_server.run()
