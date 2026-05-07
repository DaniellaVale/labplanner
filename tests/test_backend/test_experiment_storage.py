from app.models import (
    DoeRequest,
    ExperimentCreate,
    FactorLevel,
)
from app.services import experiments_storage as storage


def test_save_list_load_and_update_experiment(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "BASE_DIR", tmp_path)
    storage.BASE_DIR.mkdir(parents=True, exist_ok=True)

    payload = ExperimentCreate(
        name="teste",
        description="experimento de teste",
        doe_request=DoeRequest(
            design_type="fatorial_2k",
            factors=2,
            replicates=1,
            center_points=0,
            levels=[
                FactorLevel(name="X1", minimum=0, maximum=10),
                FactorLevel(name="X2", minimum=0, maximum=20),
            ],
        ),
    )

    doe_result = {
        "design_type": "fatorial_2k",
        "design_notation": "2^2",
        "matrix": [[-1, -1], [-1, 1], [1, -1], [1, 1]],
        "matrix_real": [[0, 0], [0, 20], [10, 0], [10, 20]],
        "rows": 4,
        "factors": 2,
        "factor_names": ["X1", "X2"],
        "fractionality": None,
    }

    exp = storage.save_new_experiment(payload, doe_result)

    summaries = storage.list_experiments()
    assert len(summaries) == 1
    assert summaries[0].id == exp.id
    assert summaries[0].name == "teste"

    loaded = storage.load_experiment(exp.id)
    assert loaded.id == exp.id
    assert loaded.name == "teste"
    assert loaded.doe_result.rows == 4
    assert len(loaded.doe_result.matrix) == 4

    updated = storage.update_experiment_responses(exp.id, [10.0, 12.0, 14.0, 16.0])
    assert updated.responses == [10.0, 12.0, 14.0, 16.0]

    reloaded = storage.load_experiment(exp.id)
    assert reloaded.responses == [10.0, 12.0, 14.0, 16.0]