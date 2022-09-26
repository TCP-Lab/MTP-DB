import logging
import aiosqlite
from aiosqlite import Connection

from daedalus import SCHEMA

log = logging.getLogger(__name__)

async def make_empty(connection: Connection) -> None:
    await connection.executescript(SCHEMA)

async def populate_gene_keys(connection):
    pass

async def generate_database(anchor):
    async with aiosqlite.connect(anchor) as connection:
        await make_empty(connection)

        await populate_gene_keys(connection)
