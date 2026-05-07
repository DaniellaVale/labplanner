from app.services.plotting import generate_pareto


def test_pareto_plot_generation(tmp_path):
    terms = [
        {"term": "Intercepto", "value": 10.0},
        {"term": "X1", "value": 2.0},
        {"term": "X2", "value": 1.0},
        {"term": "X1X2", "value": 0.5},
    ]

    file = tmp_path / "pareto.png"

    generate_pareto(terms, file)

    assert file.exists()