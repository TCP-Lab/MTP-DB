import logging
import sqlite3
from pathlib import Path
from sqlite3 import Connection

from daedalus import SCHEMA

log = logging.getLogger(__name__)


def make_empty(connection: Connection) -> None:
    connection.executescript(SCHEMA)


def generate_database(path: Path, auth_hash) -> None:
    with sqlite3.connect(path) as connection:
        make_empty(connection)
