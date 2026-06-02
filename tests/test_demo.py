from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ok"


def test_demo_start():
    client.post("/v1/demo/reset")
    resp = client.post("/v1/demo/start")
    data = resp.json()
    assert data["data"]["currentStep"] == 1
    assert data["data"]["step"]["action"] == "create_session"


def test_demo_next():
    client.post("/v1/demo/reset")
    client.post("/v1/demo/start")
    resp = client.post("/v1/demo/next")
    assert resp.json()["data"]["currentStep"] == 2


def test_demo_full_flow():
    client.post("/v1/demo/reset")
    client.post("/v1/demo/start")
    for _ in range(10):
        client.post("/v1/demo/next")
    resp = client.get("/v1/demo/current")
    assert resp.json()["data"]["status"] == "done"


def test_demo_pause():
    client.post("/v1/demo/reset")
    client.post("/v1/demo/start")
    resp = client.post("/v1/demo/pause")
    assert resp.json()["data"]["paused"]


def test_mock_weather():
    resp = client.get("/v1/mock/weather")
    assert resp.json()["data"]["source"] == "mock"


def test_mock_location():
    resp = client.get("/v1/mock/locations/LS-001")
    assert resp.json()["data"]["location"]["lat"] == 31.422
