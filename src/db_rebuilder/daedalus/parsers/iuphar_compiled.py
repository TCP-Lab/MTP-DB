import logging

from daedalus.utils import recast, to_transaction

log = logging.getLogger(__name__)

## NOTE: I don't add docstrings for these functions as they are a bit redundant:
# Imagine that the typical docstring is "Parses the input data to digested data
# for the database".


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
