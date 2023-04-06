import logging

import pandas as pd
from daedalus.utils import lmap, split_ensembl_ids, to_transaction

log = logging.getLogger(__name__)

## NOTE: I don't add docstrings for these functions as they are a bit redundant:
# Imagine that the typical docstring is "Parses the input data to digested data
# for the database".


def get_gene_ids_transaction(mart_data):
    log.info("Making gene_ids table transaction")
    ensg = mart_data["IDs+desc"]["ensembl_gene_id_version"]
    ensg = pd.unique(ensg)

    log.info("Parsing ensembl gene IDs")
    ensg = list(map(split_ensembl_ids, ensg))

    gene_ids = pd.DataFrame(
        {
            "ensg_version": lmap(lambda x: x.full_id, ensg),
            "ensg": lmap(lambda x: x.full_id_no_version, ensg),
            "ensg_version_leaf": lmap(lambda x: x.version_number, ensg),
        }
    )

    log.info("Making transaction...")
    return to_transaction(gene_ids, "gene_ids")


def get_gene_names_transaction(mart_data):
    desc_data: pd.DataFrame = mart_data["IDs+desc"][
        ["ensembl_gene_id_version", "description"]
    ]
    hugo_data: pd.DataFrame = mart_data["hugo_symbols"]

    desc_data = desc_data.drop_duplicates()

    # Merge the ensg and the data
    log.info("Merging ensembl gene IDs with HUGO symbols...")
    data = hugo_data.merge(desc_data, on="ensembl_gene_id_version")

    # Get rid of the descriptions
    data = pd.DataFrame(
        {
            "ensg": lmap(
                lambda x: split_ensembl_ids(x).full_id_no_version,
                data["ensembl_gene_id_version"],
            ),
            "hugo_gene_id": data["hgnc_id"],
            "hugo_gene_symbol": data["hgnc_symbol"],
            "gene_symbol_synonyms": pd.NA,
            "hugo_gene_name": data["description"],
        }
    )

    log.warning("IMPOSSIBLE TO FIND GENE SYNONYMS.")
    # TODO:: sanity checks?

    data = data.drop_duplicates()

    return to_transaction(data, "gene_names")
