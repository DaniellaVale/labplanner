from app.services.analysis import regression_analysis


def test_regression_basic():

    matrix = [
        [-1, -1],
        [-1, 1],
        [1, -1],
        [1, 1],
        [-1, -1],
        [-1, 1],
        [1, -1],
        [1, 1],
    ]

    responses = [
        10,
        12,
        14,
        16,
        11,
        13,
        15,
        17,
    ]

    result = regression_analysis(matrix, responses)

    assert "terms" in result
    assert "anova" in result
    assert "diagnostics" in result
    assert "r_squared" in result


def test_r_squared_range():

    matrix = [
        [-1, -1],
        [-1, 1],
        [1, -1],
        [1, 1],
        [-1, -1],
        [-1, 1],
        [1, -1],
        [1, 1],
    ]

    responses = [10, 11, 14, 16, 9, 12, 15, 18]

    result = regression_analysis(matrix, responses)

    r2 = result["r_squared"]

    assert 0 <= r2 <= 1


def test_anova_presence():

    matrix = [
        [-1, -1],
        [-1, 1],
        [1, -1],
        [1, 1],
        [-1, -1],
        [-1, 1],
        [1, -1],
        [1, 1],
    ]

    responses = [10, 12, 14, 16, 11, 13, 15, 17]

    result = regression_analysis(matrix, responses)

    anova = result["anova"]

    assert isinstance(anova, list)
    assert len(anova) > 0

    row = anova[0]

    assert "source" in row
    assert "df" in row
    assert "ss" in row


def test_saturated_model():

    matrix = [
        [-1, -1],
        [-1, 1],
        [1, -1],
        [1, 1],
    ]

    responses = [10, 12, 14, 16]

    result = regression_analysis(matrix, responses)

    assert result["is_saturated_model"] is True