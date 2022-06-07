import pytest
from httpx import AsyncClient
from abc import ABC


class Base(ABC):
    @pytest.fixture(scope="class", autouse=False)
    def url(self, request) -> str:
        self.url = 'http://localhost:3000'
        request.cls.url = self.url
        yield self.url

    @pytest.fixture(scope="class", autouse=False)
    def index(self, request) -> str:
        self.index = "/"
        request.cls.index = self.index
        yield self.index

    @pytest.fixture(scope="class", autouse=False)
    def info(self, request) -> str:
        self.info = "/v1/info"
        request.cls.info = self.info
        yield self.info

    @pytest.fixture(scope="class", autouse=False)
    def rand(self, request) -> str:
        self.rand = "/v1/random-number"
        request.cls.rand = self.rand
        yield self.rand


@pytest.mark.usefixtures("url", "index", "info", "rand")
class TestAPI(Base):
    @pytest.mark.anyio
    async def test_base_call(self):
        async with AsyncClient(base_url=self.url) as ac:
            response = await ac.get(self.index)
        assert response.status_code == 200
        assert response.json() == {"Status": 200, "Message": "Welcome"}

    @pytest.mark.anyio
    async def test_info_call(self):
        async with AsyncClient(base_url=self.url) as ac:
            response = await ac.post(self.info, json={"msg": "PYTEST TEST MESSAGE", "num": 5})
        assert response.status_code == 200
        assert response.json() == {"Status": 200, "Message": "PYTEST TEST MESSAGE", "Number": 5}

    @pytest.mark.anyio
    async def test_rand_call(self):
        async with AsyncClient(base_url=self.url) as ac:
            response = await ac.post(self.rand, json={"n": 100})
        assert response.status_code == 200
        assert response.json() == {"Status": 200, "Message": "Random Number Sent 100"}
