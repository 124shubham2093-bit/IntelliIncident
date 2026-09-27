import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure root directory is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app.main import app
from backend.app.db.database import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
