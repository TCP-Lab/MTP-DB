import pytest
from aiosqlite import Cursor

from daedalus.tests.fixtures import *
from daedalus.make_db import make_empty

## Most of these tests are useless, or nearly useless, but I wanted to try out
# pytest in an async setting, and with a database too.

@pytest.mark.usefixtures("setup_db")
async def test_schema(session: Cursor):

    tables = await session.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = await tables.fetchall()

    tables = [x[0] for x in tables]

    assert tables == ["gene_ids", "transcript_ids", "gene_names", "iuphar_ids", "iuphar_ligands", "iuphar_interaction", "tcdb_ids", "tcdb_subfamily", "tcdb_families", "gene_ontology", "channels", "carriers"]

@pytest.mark.usefixtures("setup_db")
async def test_mock_data_was_inserted(session: Cursor):
    res = await session.execute("SELECT * FROM gene_names")
    res = await res.fetchall()

    assert res != []

@pytest.mark.usefixtures("setup_db")
async def test_make_empty(session: Cursor):
    expected_schema = await session.execute("SELECT * FROM sqlite_master")
    expected_schema = await expected_schema.fetchall()

    async with aiosqlite.connect(":memory:") as new_conn:
        await make_empty(new_conn)
        test_schema = await new_conn.execute("SELECT * FROM sqlite_master")
        test_schema = await test_schema.fetchall()

    assert test_schema == expected_schema
    