import pytest
import sys
sys.path.insert(0, "src")

from app import app


@pytest.fixture
def client():
    """Create test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index(client):
    """Test index endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json["message"] == "Hello, Databricks-IoT!"


def test_health(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"
