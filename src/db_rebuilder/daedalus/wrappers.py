import functools
import aiosqlite

from daedalus import DB_PATH

connect = functools.partial(aiosqlite.connect, database = DB_PATH)

async def get_schema():
    async with connect() as conn:
        res = await conn.execute("PRAGMA table_list;")
        res = await res.fetchall()
    
    return res
