from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_full_flow():
    payload = {
        "name": "Fluxo completo",
        "doe_request": {
            "design_type": "fatorial_2k",
            "factors": 2,
            "replicates": 2,
            "center_points": 0,
            "levels": [
                {"name": "X1", "minimum": 0, "maximum": 10},
                {"name": "X2", "minimum": 0, "maximum": 20},
            ],
        },
    }

    r = client.post("/experiments", json=payload)
    assert r.status_code == 200

    experiment = r.json()
    exp_id = experiment["id"]

    r2 = client.get(f"/experiments/{exp_id}")
    assert r2.status_code == 200

    data = r2.json()
    assert "doe_result" in data
    assert len(data["doe_result"]["matrix"]) == 8

    responses_payload = {
        "responses": [10, 11, 12, 13, 14, 15, 16, 17]
    }

    r3 = client.put(f"/experiments/{exp_id}/responses", json=responses_payload)
    assert r3.status_code == 200
    saved = r3.json()
    assert saved["responses"] == responses_payload["responses"]

    r4 = client.get(f"/experiments/{exp_id}/analysis")
    assert r4.status_code == 200

    analysis = r4.json()
    assert "terms" in analysis
    assert "anova" in analysis
    assert "diagnostics" in analysis
    assert "r_squared" in analysis