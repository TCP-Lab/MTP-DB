import json
import sqlite3
from pathlib import Path

import pytest

from daedalus import SCHEMA


@pytest.fixture
def session():
    connection = sqlite3.connect(":memory:")
    yield connection
    connection.close()


@pytest.fixture
def setup_db(session):
    session.executescript(SCHEMA)
    session.executescript(Path("/app/daedalus/tests/mock_data.sql").read_text())
    session.commit()


@pytest.fixture
def secrets():
    with Path("/app/daedalus/tests/secrets.json").open("r") as file:
        secret_data = json.load(file)

    return secret_data
