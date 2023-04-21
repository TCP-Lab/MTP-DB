import logging

from daedalus.utils import (
    apply_thesaurus,
    explode_on,
    get_local_csv,
    recast,
    to_transaction,
)

log = logging.getLogger(__name__)

## NOTE: I don't add docstrings for these functions as they are a bit redundant:
# Imagine that the typical docstring is "Parses the input data to digested data
# for the database".


def get_atp_driven_carriers_transaction(hugo):
    data = recast(hugo["atpases"], {"Ensembl gene ID": "ensg"}).drop_duplicates()

    log.info("Dropping AAA - Atpases since they are not transporters...")
    p = len(data["ensg"])
    aaa_atpases = recast(hugo["AAA_atpases"], {"Ensembl gene ID": "ensg"})
    data = data.drop(data[data["ensg"].isin(aaa_atpases["ensg"])].index)
    log.info(f"Dropped {p - len(data['ensg'])} entries.")

    log.info("Adding local annotations")
    local = get_local_csv("atp_driven_ABC_data.csv")

    local = recast(
        local,
        {
            "ensg": "ensg",
            "transported_solute": "carried_solute",
            "rate": "rate",
            "direction": "direction",
            "stoichiometry": "stoichiometry",
        },
    )

    local = explode_on(local, on=";", columns=["carried_solute", "direction"])

    data = data.merge(local, how="left", on="ensg")

    data = apply_thesaurus(data)

    return to_transaction(data, "atp_driven_transporters")


def get_abc_transporters_transaction(hugo):
    data = recast(
        hugo["ABC_transporters"], {"Ensembl gene ID": "ensg"}
    ).drop_duplicates()

    log.info("Adding local annotations")
    local = get_local_csv("atp_driven_ABC_data.csv")

    local = recast(
        local,
        {
            "ensg": "ensg",
            "transported_solute": "carried_solute",
            "rate": "rate",
            "direction": "direction",
            "stoichiometry": "stoichiometry",
        },
    )

    local = explode_on(local, on=";", columns=["carried_solute", "direction"])

    data = data.merge(local, how="left", on="ensg")

    data = apply_thesaurus(data)

    return to_transaction(data, "ABC_transporters")
