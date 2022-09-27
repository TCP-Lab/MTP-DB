
from daedalus.make_db import generate_database

def test_run():
    generate_database(":memory:")
