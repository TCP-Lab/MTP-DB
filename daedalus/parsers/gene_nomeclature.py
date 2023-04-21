import logging

import pandas as pd

from daedalus.utils import lmap, recast, sanity_check, split_ensembl_ids, to_transaction

log = logging.getLogger(__name__)

## NOTE: I don't add docstrings for these functions as they are a bit redundant:
# Imagine that the typical docstring is "Parses the input data to digested data
# for the database".


def get_gene_ids_transaction(mart_data):
    log.info("Making gene_ids table transaction")
    # This frame is just ENSGs but split into their components.
    # The `split_ensembl_ids` function does the heavy lifting.
    ensg = mart_data["IDs"]["gene_stable_id_version"]
    ensg = pd.unique(ensg)

    log.info("Parsing ensembl gene IDs")
    ensg = lmap(split_ensembl_ids, ensg)

    gene_ids = pd.DataFrame(
        {
            "ensg_version": lmap(lambda x: x.full_id, ensg),
            "ensg": lmap(lambda x: x.full_id_no_version, ensg),
            "ensg_version_leaf": lmap(lambda x: x.version_number, ensg),
        }
    )

    sanity_check(
        gene_ids.notna().all(axis=None), "There are no NAs in the gene_ids frame"
    )
    return to_transaction(gene_ids, "gene_ids")


def get_gene_names_transaction(mart_data):
    # As above, this is pretty easy to do, we just need a recast:
    data = recast(
        mart_data["gene_names"],
        {
            "gene_stable_id_version": "ensg",
            "hgnc_symbol": "hugo_gene_symbol",
            "hgnc_id": "hugo_gene_id",
            "gene_description": "hugo_gene_name",
        },
    )

    # Drop the version
    data["ensg"] = lmap(lambda x: split_ensembl_ids(x).full_id_no_version, data["ensg"])

    # We currently cannot populate this col:
    # data["gene_symbol_synonyms"]
    log.warning("IMPOSSIBLE TO FIND GENE SYNONYMS.")

    return to_transaction(data, "gene_names")
