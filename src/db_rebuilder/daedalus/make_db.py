import logging
import sqlite3
from functools import partial
from pathlib import Path
from sqlite3 import Connection

from daedalus import SCHEMA
from daedalus.retrievers import (
    ResourceCache,
    retrieve_biomart,
    retrieve_cosmic_genes,
    retrieve_iuphar,
    retrieve_tcdb,
)

log = logging.getLogger(__name__)


def make_empty(connection: Connection) -> None:
    connection.executescript(SCHEMA)


def generate_database(path: Path, auth_hash) -> None:
    log.info("Making new database.")
    log.info(f"Cosmic hash: {auth_hash}")
    with sqlite3.connect(path / "db.sqlite") as connection:
        make_empty(connection)

    retrieve_cosmic_wrapper = partial(retrieve_cosmic_genes, auth_hash)

    hooks = {
        "cosmic_genes": retrieve_cosmic_wrapper,
        "biomart": retrieve_biomart,
        "iuphar": retrieve_iuphar,
        "tcdb": retrieve_tcdb,
    }

    resource_cache = ResourceCache(hooks)

    with resource_cache("cosmic_genes") as cosmic_data:
        for key, value in cosmic_data.items():
            value.to_csv(f"/app/out/cosmic_{key}.csv")

    with resource_cache("biomart") as biomart:
        for key, value in biomart.items():
            value.to_csv(f"/app/out/dump/biomart_{key}.csv")

    with resource_cache("iuphar") as iuphar:
        for key, value in iuphar.items():
            value.to_csv(f"/app/out/dump/iuphar_{key}.csv")

    with resource_cache("tcdb") as tcdb:
        for key, value in tcdb.items():
            value.to_csv(f"/app/out/dump/tcdb_{key}.csv")
