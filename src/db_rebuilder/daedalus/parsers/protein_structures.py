import logging

from daedalus.utils import lmap, recast, split_ensembl_ids, to_transaction

log = logging.getLogger(__name__)

## NOTE: I don't add docstrings for these functions as they are a bit redundant:
# Imagine that the typical docstring is "Parses the input data to digested data
# for the database".


def get_protein_structures_transaction(mart_data):
    ids = recast(
        mart_data["proteins"],
        {
            "transcript_stable_id_version": "enst",
            "protein_stable_id_version": "ensp",
            "pdb_id": "pdb_id",
            "refseq_peptide_id": "refseq_protein_id",
        },
    )

    log.info("Purging ensembl versions...")
    ids["enst"] = lmap(lambda x: split_ensembl_ids(x).full_id_no_version, ids["enst"])
    ids["ensp"] = lmap(lambda x: split_ensembl_ids(x).full_id_no_version, ids["ensp"])

    ids = ids.drop_duplicates()

    return to_transaction(ids, "protein_ids")
