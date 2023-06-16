import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def test_client():
    with TestClient(app) as c:
        yield c
