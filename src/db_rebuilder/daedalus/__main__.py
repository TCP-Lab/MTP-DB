from daedalus import OUT_ANCHOR
from daedalus.make_db import generate_database
import asyncio

asyncio.run(generate_database(OUT_ANCHOR))
