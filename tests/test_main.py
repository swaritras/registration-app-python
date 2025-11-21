from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_index():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"

def test_register_missing_email():
    r = client.post("/register", json={})
    assert r.status_code == 422  # pydantic validation error for missing email
