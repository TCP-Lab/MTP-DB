from daedalus.make_db import generate_database
from daedalus.tests.fixtures import secrets

def test_run(secrets):
    generate_database(":memory:", secrets["cosmic_hash"])
