import logging

import pandas as pd

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
    local = get_local_csv("atp_driven_data.csv")

    local = recast(
        local,
        {
            "ensg": None,
            "transported_solute": "carried_solute",
            "rate": None,
            "direction": None,
            "stoichiometry": None,
        },
    )

    local = explode_on(local, on=";", columns=["carried_solute", "direction"])

    data = data.merge(local, how="left", on="ensg")

    def drop_useless_duplicates(frame: pd.DataFrame) -> pd.DataFrame:
        if frame.shape[0] > 1:
            # If there is just one row, we have nothing to do.
            # If there is more than one row, this must be because there is some
            # solute info. This means that any rows with NA as a solute must be
            # dropped (as there is at least one other col with non-NA values)
            frame = frame.dropna(subset="carried_solute")

        return frame.drop(columns="ensg")

    log.info("Dropping useless duplicates...")
    data = (
        data.groupby(["ensg"], group_keys=True)
        .apply(drop_useless_duplicates)
        .reset_index(level="ensg")
    )

    data = apply_thesaurus(data)

    return to_transaction(data, "pumps")


def get_abc_transporters_transaction(hugo):
    data = recast(
        hugo["ABC_transporters"], {"Ensembl gene ID": "ensg"}
    ).drop_duplicates()

    log.info("Adding local annotations")
    local = get_local_csv("atp_driven_data.csv")

    local = recast(
        local,
        {
            "ensg": None,
            "transported_solute": "carried_solute",
            "rate": None,
            "direction": None,
            "stoichiometry": None,
        },
    )

    local = explode_on(local, on=";", columns=["carried_solute", "direction"])

    data = data.merge(local, how="left", on="ensg")

    def drop_useless_duplicates(frame: pd.DataFrame) -> pd.DataFrame:
        if frame.shape[0] > 1:
            # If there is just one row, we have nothing to do.
            # If there is more than one row, this must be because there is some
            # solute info. This means that any rows with NA as a solute must be
            # dropped (as there is at least one other col with non-NA values)
            frame = frame.dropna(subset="carried_solute")

        return frame.drop(columns="ensg")

    log.info("Dropping useless duplicates...")
    data = (
        data.groupby(["ensg"], group_keys=True)
        .apply(drop_useless_duplicates)
        .reset_index(level="ensg")
    )

    data = apply_thesaurus(data)

    return to_transaction(data, "ABC_transporters")
