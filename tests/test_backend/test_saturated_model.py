from app.services.analysis import regression_analysis


def test_saturated_model_detection():

    matrix = [
        [-1, -1],
        [-1, 1],
        [1, -1],
        [1, 1],
    ]

    responses = [10, 12, 14, 16]

    result = regression_analysis(matrix, responses)

    assert result["is_saturated_model"] is True