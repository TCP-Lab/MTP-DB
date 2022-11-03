import pytest
from daedalus.make_db import generate_database
from daedalus.tests.fixtures import secrets


@pytest.mark.slow
def test_run(secrets):
    generate_database("/app/test.db", secrets["cosmic_hash"])
