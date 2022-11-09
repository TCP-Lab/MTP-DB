import logging

import pandas as pd
from daedalus.utils import split_ensembl_ids, to_transaction

log = logging.getLogger(__name__)


def get_gene_ids_transaction(mart_data):
    log.info("Making gene_ids table transaction")
    ensg = mart_data["IDs+desc"]["ensembl_gene_id_version"]
    ensg = pd.unique(ensg)

    log.info("Parsing ensembl gene IDs")
    ensg = list(map(split_ensembl_ids, ensg))

    gene_ids = pd.DataFrame(
        {
            "ensg_version": list(map(lambda x: x.full_id, ensg)),
            "ensg": list(map(lambda x: x.full_id_no_version, ensg)),
            "ensg_version_leaf": list(map(lambda x: x.version_number, ensg)),
        }
    )

    log.info("Making transaction...")
    return to_transaction(gene_ids, "gene_ids")
