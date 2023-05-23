import json
import sqlite3
from pathlib import Path

import pytest

from daedalus.utils import get_local_bytes
from tests.mock_data import MOCK_DATA


@pytest.fixture
def session():
    connection = sqlite3.connect(":memory:")
    yield connection
    connection.close()


@pytest.fixture
def setup_db(session):
    setup = get_local_bytes("schema.sql").read().decode("UTF-8")
    session.executescript(setup)
    session.executescript(MOCK_DATA)
    session.commit()


@pytest.fixture
def secrets():
    with Path("/app/daedalus/tests/secrets.json").open("r") as file:
        secret_data = json.load(file)

    return secret_data
