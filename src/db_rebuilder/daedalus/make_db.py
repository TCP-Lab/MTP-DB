import logging
from pathlib import Path

from daedalus.wrappers import connect
from daedalus import SCHEMA

log = logging.getLogger(__name__)

async def make_empty() -> None:
    script = Path("/app/schema.sql").read_text()

    async with connect() as conn:
        await conn.executescript(SCHEMA)


async def generate_database():
    await make_empty()
