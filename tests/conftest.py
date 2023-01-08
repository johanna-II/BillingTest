import pytest


def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="alpha", help="alpha, beta")
    parser.addoption("--member", action="store", default="kr", help="kr, jp and etc")
    parser.addoption("--month", action="store", default="2021-05", help="test target month")


@pytest.fixture(scope="class")
def env(request):
    return request.config.getoption("--env")


@pytest.fixture(scope="class")
def member(request):
    return request.config.getoption("--member")


@pytest.fixture(scope="class")
def month(request):
    return request.config.getoption("--month")
