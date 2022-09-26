
from daedalus.make_db import generate_database

async def test_run():
    await generate_database(":memory:")
