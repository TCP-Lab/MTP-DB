import logging

import pandas as pd
from daedalus.utils import lmap, recast, split_ensembl_ids, to_transaction

log = logging.getLogger(__name__)

## NOTE: I don't add docstrings for these functions as they are a bit redundant:
# Imagine that the typical docstring is "Parses the input data to digested data
# for the database".


def get_protein_structures_transaction(mart_data):
    proteins = pd.DataFrame(
        {
            "enst": lmap(
                lambda x: split_ensembl_ids(x).full_id_no_version,
                mart_data["IDs+desc"]["ensembl_transcript_id_version"],
            ),
            "pdb_id": mart_data["IDs+desc"]["pdb"],
        }
    )

    ids = recast(
        mart_data["IDs"],
        {
            "ensembl_transcript_id": "enst",
            "ensembl_peptide_id": "ensp",
            "refseq_peptide": "refseq_protein_id",
        },
    )

    log.info("Adding refseq and ensp data...")
    proteins = proteins.merge(ids, on=["enst"])

    proteins = proteins.drop_duplicates()

    return to_transaction(proteins, "protein_ids")
