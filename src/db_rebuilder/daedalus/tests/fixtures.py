
import sqlite3
import pytest

from daedalus import SCHEMA
from pathlib import Path

@pytest.fixture
def session():
    connection = sqlite3.connect(':memory:')
    yield connection
    connection.close()


@pytest.fixture
def setup_db(session):
    session.executescript(SCHEMA)
    session.executescript(Path("/app/daedalus/tests/mock_data.sql").read_text())
    session.commit()
