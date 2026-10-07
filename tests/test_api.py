import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)
SAMPLE = json.loads((Path(__file__).parent / "sample_input.json").read_text())


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_predict():
    r = client.post("/predict", json={"features": SAMPLE})
    assert r.status_code == 200
    body = r.json()
    assert 0.0 <= body["heart_disease_probability"] <= 1.0
    assert body["prediction"] in (0, 1)
