from sqlite3 import Cursor

import pytest

from daedalus.make_db import make_empty
from tests.fixtures import *


@pytest.mark.usefixtures("setup_db")
def test_schema(session: Cursor):
    tables = session.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = tables.fetchall()

    tables = [x[0] for x in tables]

    assert tables == [
        "gene_ids",
        "transcript_ids",
        "gene_names",
        "iuphar_ids",
        "iuphar_ligands",
        "iuphar_interaction",
        "tcdb_ids",
        "tcdb_subfamily",
        "tcdb_families",
        "gene_ontology",
        "channels",
        "carriers",
    ]


@pytest.mark.usefixtures("setup_db")
def test_mock_data_was_inserted(session: Cursor):
    res = session.execute("SELECT * FROM gene_names")
    res = res.fetchall()

    assert res != []


@pytest.mark.usefixtures("setup_db")
def test_make_empty(session: Cursor):
    expected_schema = session.execute("SELECT * FROM sqlite_master")
    expected_schema = expected_schema.fetchall()

    with sqlite3.connect(":memory:") as new_conn:
        make_empty(new_conn)
        test_schema = new_conn.execute("SELECT * FROM sqlite_master")
        test_schema = test_schema.fetchall()

    assert test_schema == expected_schema
