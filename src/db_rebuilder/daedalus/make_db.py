import gc
import logging
import pickle
import sqlite3
from functools import partial
from pathlib import Path
from sqlite3 import Connection

from daedalus import SCHEMA
from daedalus.errors import Abort
from daedalus.parsers import (
    get_abc_transporters_transaction,
    get_aquaporins_transaction,
    get_atp_driven_carriers_transaction,
    get_cosmic_transaction,
    get_gene_ids_transaction,
    get_gene_names_transaction,
    get_ion_channels_transaction,
    get_iuphar_interaction_transaction,
    get_iuphar_ligands_transaction,
    get_iuphar_targets_transaction,
    get_protein_structures_transaction,
    get_refseq_transaction,
    get_solute_carriers_transaction,
    get_tcdb_definitions_transactions,
    get_tcdb_ids_transaction,
    get_transcripts_ids_transaction,
)
from daedalus.retrievers import (
    ResourceCache,
    retrieve_biomart,
    retrieve_cosmic_genes,
    retrieve_hugo,
    retrieve_iuphar,
    retrieve_iuphar_compiled,
    retrieve_slc,
    retrieve_tcdb,
)
from daedalus.utils import execute_transaction

log = logging.getLogger(__name__)


def make_empty(connection: Connection) -> None:
    """Run the db schema on a connection

    Most often, it is run on an empty database, hence the name "make_empty".

    Args:
        connection (Connection): The sqlite connection to use.
    """
    connection.executescript(SCHEMA)


def generate_database(path: Path, auth_hash) -> None:
    """Generate the database - downloading and parsing all the data.

    Fails if a db already exist in the target path.

    Args:
        path (Path): The path to generate the database to. Has to point to a folder.
            It will always be "db.sqlite".
        auth_hash (str): The COSMIC authentication hash used to log in to the COSMIC
            server to download the COSMIC data.
    """
    log.info("Making new database.")

    database_path = path / "db.sqlite"

    if database_path.exists():
        log.error("Database already exists: Refusing to overwrite.")
        raise Abort

    log.info("Executing schema...")
    with sqlite3.connect(database_path) as connection:
        make_empty(connection)

    retrieve_cosmic_wrapper = partial(retrieve_cosmic_genes, auth_hash)
    cache = ResourceCache(
        hooks={
            "biomart": retrieve_biomart,
            "cosmic": retrieve_cosmic_wrapper,
            "iuphar": retrieve_iuphar,
            "iuphar_compiled": retrieve_iuphar_compiled,
            "tcdb": retrieve_tcdb,
            "hugo": retrieve_hugo,
            "slc": retrieve_slc,
        }
    )

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

    log.info("Connecting to empty database...")
    connection = sqlite3.connect(database_path, isolation_level=None)

    log.info("Populating database with data...")
    populate_database(connection, cache)

    apply_manual_tweaks(
        connection, sql_folder_path=Path("./daedalus/post_build_hooks/").resolve()
    )

    connection.close()
    log.info(f"Finished populating database. Saved in {database_path}")


def apply_manual_tweaks(connection: Connection, sql_folder_path: Path):
    log.info("Looking for post-build transactions...")
    if not sql_folder_path.is_dir():
        raise ValueError(f"Supplied path {sql_folder_path} is not a directory.")

    to_apply: list[Path] = []
    for item in sql_folder_path.iterdir():
        if item.is_file() and item.suffix.lower() == ".sql":
            to_apply.append(item)

    if not to_apply:
        log.info("Found no transactions to apply.")
        return

    to_apply.sort()
    # The files are appended in the opposite order, but I want to execute them
    # in order.

    log.info(f"Found {len(to_apply)} hooks to apply.")
    for item in to_apply:
        with item.open("r") as stream:
            sql = stream.read()
            # There might be multiple statements in one file
            # We can split it up here and execute them one at a time
            sql_parts = [f"{x};" for x in sql.split(";") if x.strip()]
            for i, transaction in enumerate(sql_parts):
                log.info(f"Executing post-build hook {item.name} [{i + 1}]...")
                execute_transaction(connection, transaction)


def populate_database(connection: Connection, cache: ResourceCache) -> None:
    """Populate an empty database with data

    The database has to be initialized with the schema.

    Args:
        connection (Connection): The connection to act upon
        cache (ResourceCache): The cache with the data used by the parsers.
    """
    # Debugging purposes
    SUPPRESS_ALL = True

    # Suppress_all controls all the debug guards, the False is there to
    # override the suppress_all
    if (not SUPPRESS_ALL) or False:
        ## -- gene_ids table --
        log.info("Populating IDs...")
        with cache("biomart") as mart_data:
            transaction = get_gene_ids_transaction(mart_data)

            execute_transaction(connection, transaction)

        gc.collect()
    else:
        log.debug("Skipped populating IDs.")

    if (not SUPPRESS_ALL) or False:
        ## -- transcript_ids table --
        log.info("Populating transcript IDs...")
        with cache("biomart") as mart_data:
            transaction = get_transcripts_ids_transaction(mart_data)

            execute_transaction(connection, transaction)

        gc.collect()
    else:
        log.debug("Skipped populating transcript IDs.")

    if (not SUPPRESS_ALL) or False:
        ## -- mrna_refseq table --
        log.info("Populating refseq_mrna...")
        with cache("biomart") as mart_data:
            transaction = get_refseq_transaction(mart_data)

            execute_transaction(connection, transaction)

        gc.collect()
    else:
        log.debug("Skipped populating refseq_mrna.")

    if (not SUPPRESS_ALL) or False:
        ## -- protein_structures table --
        log.info("Populating pdb structure identifiers...")
        with cache("biomart") as mart_data:
            transaction = get_protein_structures_transaction(mart_data)

            execute_transaction(connection, transaction)

        gc.collect()
    else:
        log.debug("Skipped populating protein structures.")

    if (not SUPPRESS_ALL) or False:
        ## -- gene_names table --
        log.info("Populating gene names...")
        with cache("biomart") as mart_data:
            transaction = get_gene_names_transaction(mart_data)

            execute_transaction(connection, transaction)
        gc.collect()
    else:
        log.debug("Skipped populating gene names.")

    if (not SUPPRESS_ALL) or False:
        ## -- iuphar_ids --
        log.info("Populating iuphar targets...")
        with cache("iuphar_compiled") as iuphar:
            transaction = get_iuphar_targets_transaction(iuphar)

            execute_transaction(connection, transaction)
        gc.collect()
    else:
        log.debug("Skipped populating iuphar targets.")

    if (not SUPPRESS_ALL) or False:
        ## -- iuphar_ligands --
        log.info("Populating iuphar ligands...")
        with cache("iuphar_compiled") as iuphar:
            transaction = get_iuphar_ligands_transaction(iuphar)

            execute_transaction(connection, transaction)
        gc.collect()
    else:
        log.debug("Skipped populating iuphar ligands")

    if (not SUPPRESS_ALL) or False:
        ## -- iuphar_interaction --
        log.info("Populating iuphar interactions...")
        with cache("iuphar_compiled") as iuphar:
            transaction = get_iuphar_interaction_transaction(iuphar)

            execute_transaction(connection, transaction)
        gc.collect()
    else:
        log.debug("Skipped populating iuphar interactions.")

    if (not SUPPRESS_ALL) or False:
        ## -- TCDB ids --
        log.info("Populating TCDB to Ensembl IDs...")
        with cache("tcdb") as tcdb, cache("biomart") as mart_data:
            transaction = get_tcdb_ids_transaction(tcdb, mart_data)

            execute_transaction(connection, transaction),
        gc.collect()
    else:
        log.debug("Skipped populating TCDB to Ensembl IDs.")

    if (not SUPPRESS_ALL) or False:
        ## -- TCDB types / subtypes / families --
        log.info("Populating TCDB definitions...")
        with cache("tcdb") as tcdb:
            transactions = get_tcdb_definitions_transactions(tcdb)

            for trans in transactions:
                execute_transaction(connection, trans)
        gc.collect()
    else:
        log.debug("Skipped populating TCDB definitions")

    if (not SUPPRESS_ALL) or True:
        ## -- ion channels --
        log.info("Populating ion channel metadata")
        with cache("iuphar") as iuphar, cache("hugo") as hugo:
            transaction = get_ion_channels_transaction(iuphar, hugo)

            execute_transaction(connection, transaction)
        gc.collect()
    else:
        log.debug("Skipped populating ion channel metadata")

    if (not SUPPRESS_ALL) or False:
        ## -- cosmic genes --
        log.info("Populating COSMIC gene tables...")
        with cache("cosmic") as cosmic, cache("biomart") as mart_data:
            transaction = get_cosmic_transaction(cosmic, mart_data)

            execute_transaction(connection, transaction)
        gc.collect()
    else:
        log.debug("Skipped populating COSMIC tables")

    if (not SUPPRESS_ALL) or False:
        ## -- aquaporins --
        log.info("Populating aquaporins...")
        with cache("hugo") as hugo:
            transaction = get_aquaporins_transaction(hugo)
            execute_transaction(connection, transaction)
        gc.collect()
    else:
        log.debug("Skipped populating aquaporins")

    if (not SUPPRESS_ALL) or False:
        ## -- solute carriers --
        log.info("Populating solute carriers...")
        with cache("hugo") as hugo, cache("iuphar") as iuphar, cache("slc") as slc:
            transaction = get_solute_carriers_transaction(hugo, iuphar, slc)
            execute_transaction(connection, transaction)
        gc.collect()
    else:
        log.debug("Skipped populating solute carriers")

    if (not SUPPRESS_ALL) or False:
        ## ABC transporters
        log.info("Populating ABC transporters...")
        with cache("hugo") as hugo, cache("iuphar") as iuphar:
            transaction = get_abc_transporters_transaction(hugo, iuphar)
            execute_transaction(connection, transaction)
        gc.collect()
    else:
        log.debug("Skipped populating ABC transporters")

    if (not SUPPRESS_ALL) or False:
        ## atp_driven carriers
        log.info("Populating ATP-driven carriers...")
        with cache("hugo") as hugo, cache("iuphar") as iuphar:
            transaction = get_atp_driven_carriers_transaction(hugo, iuphar)
            execute_transaction(connection, transaction)
        gc.collect()
    else:
        log.debug("Skipped populating ATP-driven carriers")
