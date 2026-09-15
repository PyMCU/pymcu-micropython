from tests.parity._api import assert_case, pytest_generate_for_module


MODULE_NAME = "time"


def pytest_generate_tests(metafunc):
    pytest_generate_for_module(metafunc, MODULE_NAME)


def test_public_api_parity(case):
    assert_case(case)
