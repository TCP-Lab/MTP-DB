import gc
import logging
import pickle
import sqlite3
from functools import partial
from pathlib import Path
from sqlite3 import Connection

from daedalus import SCHEMA
from daedalus.parsers import (
    get_gene_ids_transaction,
    get_gene_names_transaction,
    get_iuphar_interaction_transaction,
    get_iuphar_ligands_transaction,
    get_iuphar_targets_transaction,
    get_protein_structures_transaction,
    get_refseq_transaction,
    get_transcripts_ids_transaction,
)
from daedalus.retrievers import (
    ResourceCache,
    retrieve_biomart,
    retrieve_cosmic_genes,
    retrieve_iuphar,
    retrieve_iuphar_compiled,
    retrieve_tcdb,
)
from daedalus.utils import execute_transaction

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
            raise

    retrieve_cosmic_wrapper = partial(retrieve_cosmic_genes, auth_hash)

    cache = ResourceCache(
        hooks={
            "biomart": retrieve_biomart,
            "cosmic": retrieve_cosmic_wrapper,
            "iuphar": retrieve_iuphar,
            "iuphar_compiled": retrieve_iuphar_compiled,
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
    connection = sqlite3.connect(path / "db.sqlite", isolation_level=None)

    ## -- gene_ids table --
    log.info("Populating IDs...")
    with cache("biomart") as mart_data:
        transaction = get_gene_ids_transaction(mart_data)

        execute_transaction(connection, transaction)

    gc.collect()

    ## -- transcript_ids table --
    log.info("Populating transcript IDs...")
    with cache("biomart") as mart_data:
        transaction = get_transcripts_ids_transaction(mart_data)

        execute_transaction(connection, transaction)

    gc.collect()

    ## -- mrna_refseq table --
    log.info("Populating refseq_mrna...")
    with cache("biomart") as mart_data:
        transaction = get_refseq_transaction(mart_data)

        execute_transaction(connection, transaction)

    gc.collect()

    ## -- protein_structures table --
    log.info("Populating pdb structure identifiers...")
    with cache("biomart") as mart_data:
        transaction = get_protein_structures_transaction(mart_data)

        execute_transaction(connection, transaction)

    ## -- gene_names table --
    log.info("Populating gene names...")
    with cache("biomart") as mart_data:
        transaction = get_gene_names_transaction(mart_data)

        execute_transaction(connection, transaction)
    gc.collect()

    ## -- iuphar_ids --
    log.info("Populating iuphar targets...")
    with cache("iuphar_compiled") as iuphar:
        transaction = get_iuphar_targets_transaction(iuphar)

        execute_transaction(connection, transaction)
    gc.collect()

    ## -- iuphar_ligands --
    log.info("Populating iuphar ligands...")
    with cache("iuphar_compiled") as iuphar:
        transaction = get_iuphar_ligands_transaction(iuphar)

        execute_transaction(connection, transaction)
    gc.collect()

    ## -- iuphar_ids --
    log.info("Populating iuphar interactions...")
    with cache("iuphar_compiled") as iuphar:
        transaction = get_iuphar_interaction_transaction(iuphar)

        execute_transaction(connection, transaction)
    gc.collect()

    connection.close()
    log.info(f"Finished populating database. Saved in {path / 'db.sqlite'}")
