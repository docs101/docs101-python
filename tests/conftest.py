import pytest

from docs101 import Docs101Client

BASE_URL = "https://docs101.com/api/v1"


@pytest.fixture
def client():
    return Docs101Client(api_key="test-key", base_url=BASE_URL)
