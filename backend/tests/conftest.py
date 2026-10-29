import os
import tempfile

# Settings are read at import time, so point them at a throwaway DB before importing the app
_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_db.name}"
os.environ["APP_PASSWORD"] = "test-pass"
os.environ["REDIS_URL"] = ""
os.environ["SCHEDULER_ENABLED"] = "false"

import fakeredis  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import cache  # noqa: E402
from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def redis():
    r = fakeredis.FakeRedis(decode_responses=True)
    cache.set_redis(r)
    yield r
    cache.set_redis(None)


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    with TestClient(app) as c:  # lifespan runs create_all
        yield c


@pytest.fixture
def user(client):
    assert client.post("/api/auth/login", json={"password": "test-pass"}).status_code == 200
    return client
