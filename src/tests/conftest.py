import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--runsecrets",
        action="store_true",
        default=False,
        help="run tests that require secrets",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")
    config.addinivalue_line(
        "markers", "download: mark tests as needing to download something"
    )
    config.addinivalue_line("markers", "secrets: mark tests as needing secrets to run")
    # logging.basicConfig(level=logging.getLevelName("WARNING"), force=True)


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--runslow"):
        skip_slow = pytest.mark.skip(reason="need --runslow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

    if not config.getoption("--runsecrets"):
        skip_slow = pytest.mark.skip(reason="need --runsecrets option to run")
        for item in items:
            if "secrets" in item.keywords:
                item.add_marker(skip_slow)
