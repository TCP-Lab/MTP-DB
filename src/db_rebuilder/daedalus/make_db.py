import gc
import logging
import pickle
import sqlite3
from functools import partial
from pathlib import Path
from sqlite3 import Connection

from daedalus import SCHEMA
from daedalus.errors import Abort
from daedalus.parsers import get_gene_ids_transaction
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
        try:
            make_empty(connection)
        except sqlite3.OperationalError:
            log.error("Database already exists. Refusing to overwrite.")
            raise Abort

    retrieve_cosmic_wrapper = partial(retrieve_cosmic_genes, auth_hash)

    cache = ResourceCache(
        hooks={
            "biomart": retrieve_biomart,
            "cosmic": retrieve_cosmic_wrapper,
            "iuphar": retrieve_iuphar,
            "tcdb": retrieve_tcdb,
        }
    )

    ## TEMP -- remove me
    # Cache the data to a pickle so that we don't download it every time
    pickle_path = path / "datacache.pickle"
    if not pickle_path.exists():
        cache.populate()
        data = cache._ResourceCache__data
        with pickle_path.open("w+b") as stream:
            pickle.dump(data, stream)
        log.info("Dumped pickled data.")
    else:
        with pickle_path.open("rb") as stream:
            data = pickle.load(stream)
        cache._ResourceCache__populated = True
        cache._ResourceCache__data = data
        log.debug("Loaded from pickled data.")
    ## TEMP -- remove me

    log.info("Connecting to empty database...")
    connection = sqlite3.connect(path / "db.sqlite")

    ## -- gene_ids table --
    log.info("Populating IDs...")
    with cache("biomart") as mart_data:
        transaction = get_gene_ids_transaction(mart_data)

        connection.execute(transaction)
        connection.commit()

    log.info("Done populating IDs. Cleaning up.")
    gc.collect()

    log.info(f"Finished populating database. Saved in {path / 'db.sqlite'}")
