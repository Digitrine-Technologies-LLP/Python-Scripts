import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--url",
        action="store",
        default="https://example.com",
        help="URL to run tests against",
    )


@pytest.fixture
def url(request):
    return request.config.getoption("--url")
