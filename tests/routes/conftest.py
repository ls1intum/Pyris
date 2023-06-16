import pytest
from app import app


@pytest.fixture(scope="module")
def test_client():
    with app.test_client() as testing_client:
        with app.app_context():
            yield testing_client
