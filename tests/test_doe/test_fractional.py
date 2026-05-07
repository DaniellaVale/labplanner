from app.api.routes_experiments import generate_fractional_2k_matrix


def test_fractional_2_3_minus_1():
    matrix = generate_fractional_2k_matrix(3, 1)

    assert len(matrix) == 4
    assert [-1, -1, 1] in matrix
    assert [-1, 1, -1] in matrix
    assert [1, -1, -1] in matrix
    assert [1, 1, 1] in matrix