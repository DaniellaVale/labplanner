from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_experiment():
    payload = {
        "name": "Experimento teste",
        "doe_request": {
            "design_type": "fatorial_2k",
            "factors": 2,
            "replicates": 1,
            "center_points": 0,
            "levels": [
                {"name": "Temperatura", "minimum": 20, "maximum": 40},
                {"name": "Tempo", "minimum": 10, "maximum": 30},
            ],
        },
    }

    response = client.post("/experiments/", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert "id" in data
    assert data["name"] == "Experimento teste"
    assert "doe_request" in data
    assert "doe_result" in data

    assert data["doe_result"]["design_type"] == "fatorial_2k"
    assert "matrix" in data["doe_result"]
    assert len(data["doe_result"]["matrix"]) == 4
    assert data["doe_result"]["rows"] == 4