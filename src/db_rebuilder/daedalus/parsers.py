import logging

import pandas as pd
from daedalus.utils import lmap, sanity_check, split_ensembl_ids, to_transaction

log = logging.getLogger(__name__)


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


def get_transcripts_ids_transaction(mart_data):
    log.info("Making transcripts_ids table transaction")
    transcript_ids = mart_data["IDs+desc"][
        ["ensembl_gene_id_version", "ensembl_transcript_id_version"]
    ]

    log.info("Dropping duplicates...")
    transcript_ids = transcript_ids.drop_duplicates(keep="first", ignore_index=True)

    log.info("Parsing ensembl IDs...")
    # this is ugly, but it applies "split_ensembl_ids" to the two cols
    parsed_versions = transcript_ids[
        ["ensembl_gene_id_version", "ensembl_transcript_id_version"]
    ].applymap(split_ensembl_ids)

    sanity_check(
        (
            transcript_ids["ensembl_transcript_id_version"]
            == lmap(
                lambda x: x.full_id, parsed_versions["ensembl_transcript_id_version"]
            )
        ).all(),
        "ID order preserved",
    )

    log.info("Purging versions...")
    transcript_ids = pd.DataFrame(
        {
            "ensg": lmap(
                lambda x: x.full_id_no_version,
                parsed_versions["ensembl_gene_id_version"],
            ),
            "enst": lmap(
                lambda x: x.full_id_no_version,
                parsed_versions["ensembl_transcript_id_version"],
            ),
            "enst_version": lmap(
                lambda x: x.full_id, parsed_versions["ensembl_transcript_id_version"]
            ),
            "enst_version_leaf": lmap(
                lambda x: x.version_number,
                parsed_versions["ensembl_transcript_id_version"],
            ),
        }
    )

    log.info("Setting canonical isoforms...")
    transcript_ids["is_canonical_isoform"] = 0

    # Set genes with just one isoform to 1...
    single_isoforms = transcript_ids.duplicated(subset="ensg", keep=False)
    transcript_ids.loc[~single_isoforms, "is_canonical_isoform"] = 1

    # ... but some genes should still be ambiguous.
    sanity_check(
        not all(lmap(lambda x: x == 1, transcript_ids["is_canonical_isoform"])),
        "not all genes have only one isoform",
    )

    # Warn that isoform determination is still ambiguous
    log.warning(
        "Impossible to determine canonical isoforms for genes with multiple isoforms."
    )

    return to_transaction(transcript_ids, "transcript_ids")
