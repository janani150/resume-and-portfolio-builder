from fastapi.testclient import TestClient
from app.main import app


def test_root():
    client = TestClient(app)
    resp = client.get("/api/v1/auth/me")
    # No auth -> 401
    assert resp.status_code in (401, 422)
