import gc
import logging
import pickle
import sqlite3
from functools import partial
from pathlib import Path
from sqlite3 import Connection
from typing import Any, Callable, Optional

from daedalus.constants import CACHE_NAME, DB_NAME
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
from daedalus.utils import (
    execute_transaction,
    get_local_post_build_hooks,
    get_local_text,
)

log = logging.getLogger(__name__)


def make_empty(connection: Connection) -> None:
    """Run the db schema on a connection

    Most often, it is run on an empty database, hence the name "make_empty".

    Args:
        connection (Connection): The sqlite connection to use.
    """
    # A SQL "script" has a BEGIN and an END flag. Don't ask why.
    SCHEMA = "BEGIN;\n{}\nEND;".format(get_local_text("schema.sql").read())
    connection.executescript(SCHEMA)


def generate_database(
    path: Path,
    auth_hash: Optional[str],
    to_run: list[str] = [],
    to_skip: list[str] = [],
) -> None:
    """Generate the database - downloading and parsing all the data.

    Fails if a db already exist in the target path.

    Args:
        path (Path): The path to generate the database to. Has to point to a folder.
            It will always be "db.sqlite".
        auth_hash (str): The COSMIC authentication hash used to log in to the COSMIC
            server to download the COSMIC data. If None, will not populate the
            COSMIC cache. This might lead to errors if "cosmic" is not skipped.
        to_run (Optional[list[str]]): Passed to `populate_database`.
        to_skip (Optional[list[str]]): Passed to `populate_database`.
    """
    log.info("Making new database.")

    database_path = path / DB_NAME

    log.info("Executing schema...")
    with sqlite3.connect(database_path) as connection:
        make_empty(connection)

    cache_hooks = {
        "biomart": retrieve_biomart,
        "iuphar": retrieve_iuphar,
        "iuphar_compiled": retrieve_iuphar_compiled,
        "tcdb": retrieve_tcdb,
        "hugo": retrieve_hugo,
        "slc": retrieve_slc,
    }

    if auth_hash:
        retrieve_cosmic_wrapper = partial(retrieve_cosmic_genes, auth_hash)
        cache_hooks["cosmic"] = retrieve_cosmic_wrapper
    elif "cosmic" in to_skip:
        log.warning(
            "Skipped adding COSMIC data, but the 'cosmic' parser is missing. This might lead to errors."
        )

    cache = ResourceCache(hooks=cache_hooks)

    # Cache the data to a pickle so that we don't download it every time
    # TODO: this should be moved to the implementation of the ResourceCache
    # itself. It is dumb to keep it here.
    pickle_path = path / CACHE_NAME
    if not pickle_path.exists():
        cache.populate()
        data = cache._ResourceCache__data
        with pickle_path.open("w+b") as stream:
            pickle.dump(data, stream)
        log.info("Dumped pickled data.")
    else:
        with pickle_path.open("rb") as stream:
            data = pickle.load(stream)
        # Refresh the hooks
        new_hooks = {key: None for key in data.keys()}
        cache._ResourceCache__hooks = new_hooks
        cache._ResourceCache__populated = True
        cache._ResourceCache__data = data
        log.debug("Loaded from pickled data.")

    log.info("Connecting to empty database...")
    connection = sqlite3.connect(database_path, isolation_level=None)

    log.info("Populating database with data...")
    populate_database(connection, cache, to_skip=to_skip, to_run=to_run)

    log.info("Running manual tweaks...")
    apply_manual_tweaks(connection)

    connection.close()
    log.info(f"Finished populating database. Saved in {database_path}")


def apply_manual_tweaks(connection: Connection):
    log.info("Looking for post-build transactions...")
    to_apply = get_local_post_build_hooks()

    if not to_apply:
        log.info("Found no transactions to apply.")
        return

    log.info(f"Found {len(to_apply)} hooks to apply. Applying...")
    for name, item in to_apply.items():
        sql = item.read()
        # There might be multiple statements in one file
        # We can split it up here and execute them one at a time
        sql_parts = [f"{x};" for x in sql.split(";") if x.strip()]
        for i, transaction in enumerate(sql_parts):
            log.info(f"Executing post-build hook {name} [{i + 1}]...")
            execute_transaction(connection, transaction)


class Daedalus:
    def __init__(self, connection: Connection, cache: ResourceCache) -> None:
        self.connection: Connection = connection

        def get_wrapper(
            getter: Callable,
            cache: ResourceCache,
            cache_args: dict,
            other_args: dict = None,
        ) -> Any:
            """Wraps a get_x_transaction function to call the cache when appropriate"""
            cached_data = {}
            for key, value in cache_args.items():
                with cache(value) as data:
                    cached_data[key] = data

            if other_args:
                cached_data.update(other_args)

            return getter(**cached_data)

        get = partial(get_wrapper, cache=cache)

        # This might be hard to understand but bear with me:
        # - The "runners" dict has the function that need to be run to get the
        #   transaction strings to execute against the DB.
        # - However, I don't want them to be called now - I want them to be
        #   called in the `sef.run` method. So, we have to "prime" them with
        #   their args here, and then do the actual call later on.
        # - I could just use partial, but there is another problem (which I put
        #   myself into, but it's another story): the cache needs to be populated
        #   when we call the function, not before.
        # - I also need to adapt the calls to the cache with the actual signature
        #   of "get_x_transaction".
        #
        # We need 2 layer of "partials": the one in "get_wrapper" for the cache,
        # and the one out here to prep everything for the later call in `self.run`

        # I hope this helps whomever is unfortunate enough to read this later on.

        self.runners = {
            "gene_ids": partial(
                get, get_gene_ids_transaction, cache_args={"mart_data": "biomart"}
            ),
            "transcript_ids": partial(
                get,
                get_transcripts_ids_transaction,
                cache_args={"mart_data": "biomart"},
            ),
            "refseq_mrna": partial(
                get, get_refseq_transaction, cache_args={"mart_data": "biomart"}
            ),
            "protein_structures": partial(
                get,
                get_protein_structures_transaction,
                cache_args={"mart_data": "biomart"},
            ),
            "gene_names": partial(
                get, get_gene_names_transaction, cache_args={"mart_data": "biomart"}
            ),
            "iuphar_targets": partial(
                get,
                get_iuphar_targets_transaction,
                cache_args={"iuphar_casted": "iuphar_compiled"},
            ),
            "iuphar_ligands": partial(
                get,
                get_iuphar_ligands_transaction,
                cache_args={"iuphar_casted": "iuphar_compiled"},
            ),
            "iuphar_interactions": partial(
                get,
                get_iuphar_interaction_transaction,
                cache_args={"iuphar_casted": "iuphar_compiled"},
            ),
            "tcdb_ids": partial(
                get,
                get_tcdb_ids_transaction,
                cache_args={"tcdb_data": "tcdb", "mart_data": "biomart"},
            ),
            "tcdb_definitions": partial(
                get, get_tcdb_definitions_transactions, cache_args={"tcdb_data": "tcdb"}
            ),
            "ion_channels": partial(
                get,
                get_ion_channels_transaction,
                cache_args={
                    "iuphar_data": "iuphar",
                    "hugo": "hugo",
                    "iuphar_compiled": "iuphar_compiled",
                },
            ),
            "cosmic": partial(
                get,
                get_cosmic_transaction,
                cache_args={"cosmic": "cosmic", "mart_data": "biomart"},
            ),
            "aquaporins": partial(
                get, get_aquaporins_transaction, cache_args={"hugo": "hugo"}
            ),
            "solute_carriers": partial(
                get,
                get_solute_carriers_transaction,
                cache_args={"hugo": "hugo", "iuphar": "iuphar", "slc": "slc"},
            ),
            "ABC_transporters": partial(
                get,
                get_abc_transporters_transaction,
                cache_args={"hugo": "hugo"},
            ),
            "ATP_driven": partial(
                get,
                get_atp_driven_carriers_transaction,
                cache_args={"hugo": "hugo"},
            ),
        }
        """A dict with keys arbitrary names for the runners, and for values partial calls to 'get_wrapper'

        In essence, will run all the "get_wrappers" only when "self.run" is called, not before.
        """

    def run(self, to_skip: list[str] = []) -> None:
        """Run all the getters on the connection"""
        apply = partial(execute_transaction, connection=self.connection)

        for i, (key, runner) in enumerate(self.runners.items()):
            i += 1  # To count from 1, not 0
            if key not in to_skip:
                log.info(f"[ {i} / {len(self.runners)} ] Running {key}")
                transaction = runner()
                # Some 'get' (namely the TCDB stuff) gives a list of transactions,
                # so this is why we have to do this
                if isinstance(transaction, list):
                    for element in transaction:
                        apply(transaction=element)
                else:
                    apply(transaction=transaction)

                log.debug("Taking out the garbage...")
                gc.collect()
            else:
                log.info(f"[ {i} / {len(self.runners)}] Skipped {key}")


def populate_database(
    connection: Connection,
    cache: ResourceCache,
    to_skip: Optional[list[str]] = None,
    to_run: Optional[list[str]] = None,
) -> None:
    """Populate an empty database with data

    The database has to be initialized with the schema.

    Args:
        connection (Connection): The connection to act upon
        cache (ResourceCache): The cache with the data used by the parsers.
        to_skip (Optional[list[str]]): A list of strings of runners that need
          to be skipped. Cannot be passed with "to_run". Defaults to None.
        to_run(Optional[list[str]]): A list of strings of runners that need
          to be run. Cannot be passed with "to_skip". Defaults to None.
    """

    daedalus = Daedalus(connection, cache)

    if to_run and to_skip:
        log.info("Cannot accept both a 'to_skip' and 'to_run' value.")
        raise Abort

    if to_run:
        # Get the inverted set of keys to skip (NOT to_run)
        to_skip = [x for x in daedalus.runners.keys() if x not in to_run]

    if not to_run and not to_skip:
        to_skip = []

    daedalus.run(to_skip)
