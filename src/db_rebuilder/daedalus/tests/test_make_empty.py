import pytest
from aiosqlite import Cursor

from daedalus.tests.fixtures import *
from daedalus.make_db import make_empty

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

