from app.api.routes_experiments import coded_to_real


def test_coded_to_real():
    value = coded_to_real(-1, 0, 10)
    assert value == 0

    value = coded_to_real(1, 0, 10)
    assert value == 10