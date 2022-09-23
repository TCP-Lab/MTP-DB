
import pytest
import aiosqlite

from daedalus import SCHEMA
from pathlib import Path

@pytest.fixture
async def session():
    connection = await aiosqlite.connect(':memory:')
    yield connection
    await connection.close()


@pytest.fixture
async def setup_db(session):
    await session.executescript(SCHEMA)
    await session.executescript(Path("/app/daedalus/tests/mock_data.sql").read_text())
    await session.commit()
