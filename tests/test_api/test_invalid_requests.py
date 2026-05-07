from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_experiment_invalid_factors():
    payload = {
        "name": "teste erro",
        "doe_request": {
            "design_type": "fatorial_2k",
            "factors": 0,
            "levels": []
        }
    }

    r = client.post("/experiments", json=payload)

    assert r.status_code >= 400