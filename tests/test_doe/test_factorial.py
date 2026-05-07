from app.api.routes_experiments import generate_2k_matrix


def test_factorial_2k():
    matrix = generate_2k_matrix(2)

    assert len(matrix) == 4
    assert [-1, -1] in matrix
    assert [-1, 1] in matrix
    assert [1, -1] in matrix
    assert [1, 1] in matrix