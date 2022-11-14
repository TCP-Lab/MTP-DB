import logging

import pandas as pd
from daedalus.utils import lmap, recast, sanity_check, split_ensembl_ids, to_transaction

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


def get_refseq_transaction(mart_data):
    refseq = mart_data["IDs+desc"][["ensembl_transcript_id_version", "refseq_mrna"]]

    refseq = pd.DataFrame(
        {
            "refseq_transcript_id": refseq["refseq_mrna"],
            "enst": lmap(
                lambda x: split_ensembl_ids(x).full_id_no_version,
                refseq["ensembl_transcript_id_version"],
            ),
        }
    )

    refseq = refseq.drop_duplicates()

    return to_transaction(refseq, "mrna_refseq")


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


def get_iuphar_targets_transaction(iuphar_casted):
    data = recast(
        iuphar_casted["targets+families"],
        {
            "Human Ensembl Gene": "ensg",
            "Target id": "target_id",
            "Target name": "target_name",
            "Family id": "family_id",
            "Family name": "family_name",
        },
    )

    return to_transaction(data.drop_duplicates(), "iuphar_targets")


def get_iuphar_ligands_transaction(iuphar_casted):
    relevant_data = recast(
        iuphar_casted["ligands"],
        {
            "Ligand ID": "ligand_id",
            "Type": "ligand_type",
            "Name": "ligand_name",
            "Ensembl ID": "ensembl_id",
            "PubChem SID": "pubchem_sid",
            "PubChem CID": "pubchem_cid",
            "Approved": "is_approved_drug",
            "Withdrawn": "is_withdrawn_drug",
        },
    )

    return to_transaction(relevant_data.drop_duplicates(), "iuphar_ligands")


def get_iuphar_interaction_transaction(iuphar_casted):
    relevant_data = recast(
        iuphar_casted["interactions"],
        {
            "Target ID": "target_id",
            "Ligand ID": "ligand_id",
            "Approved": "is_approved_drug",
            "Action": "ligand_action",
            "Selectivity": "ligand_selectivity",
            "Endogenous": "is_endogenous",
            "Primary Target": "is_primary_target",
            "Target Species": "species",  # For filtering - drop later
        },
    )

    relevant_data = relevant_data[relevant_data["species"] == "Human"]

    relevant_data = relevant_data.drop(columns=["species"]).drop_duplicates()

    return to_transaction(relevant_data, "iuphar_interaction")


def get_tcdb_ids_transaction():
    pass
