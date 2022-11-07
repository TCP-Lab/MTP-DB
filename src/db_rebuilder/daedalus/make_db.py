import logging
import sqlite3
from functools import partial
from pathlib import Path
from sqlite3 import Connection

from daedalus import SCHEMA
from daedalus.errors import Abort
from daedalus.retrievers import (
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
        try:
            make_empty(connection)
        except FileExistsError:
            log.error("Database already exists. Refusing to overwrite.")
            raise Abort

    retrieve_cosmic_wrapper = partial(retrieve_cosmic_genes, auth_hash)

    if False:
        try:
            cosmic_data = retrieve_cosmic_wrapper()
            for key, value in cosmic_data.items():
                value.to_csv(f"/app/out/cosmic_{key}.csv")
        except Exception as e:
            log.exception(e)

    if False:
        try:
            biomart_data = retrieve_biomart()

            for key, value in biomart_data.items():
                value.to_csv(f"/app/out/biomart_{key}.csv")
        except Exception as e:
            log.exception(e)

    if False:
        try:
            iuphar = retrieve_iuphar()
            for key, value in iuphar.items():
                value.to_csv(f"/app/out/iuphar_{key}.csv")
        except Exception as e:
            log.exception(e)

    if True:
        try:
            tcdb = retrieve_tcdb()
            for key, value in tcdb.items():
                value.to_csv(f"/app/out/tcdb_{key}.csv")
        except Exception as e:
            log.exception(e)
