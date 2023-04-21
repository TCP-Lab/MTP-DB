import logging

from daedalus.utils import recast, to_transaction

log = logging.getLogger(__name__)

## NOTE: I don't add docstrings for these functions as they are a bit redundant:
# Imagine that the typical docstring is "Parses the input data to digested data
# for the database".


def get_aquaporins_transaction(hugo):
    aquaporins = recast(hugo["porins"], {"Ensembl gene ID": "ensg"}).drop_duplicates()

    log.warn("Impossible to determine tissue of expression for aquaporins.")

    return to_transaction(aquaporins, "aquaporins")
