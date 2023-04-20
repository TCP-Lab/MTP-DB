import logging
from copy import deepcopy
from math import inf
from statistics import mean
from typing import Iterable

import numpy as np
import pandas as pd

from daedalus.utils import apply_thesaurus, recast, sanity_check, to_transaction

log = logging.getLogger(__name__)

## NOTE: I don't add docstrings for these functions as they are a bit redundant:
# Imagine that the typical docstring is "Parses the input data to digested data
# for the database".


def calc_pseudo_mean(row: Iterable):
    high, low, median = row[
        ["conductance_high", "conductance_low", "conductance_median"]
    ]
    if median:
        return row

    if not high and not low:
        log.warn(f"Found missing conductance data for object ID {row['object_id']}")
        return

    if not high:
        row["conductance_median"] = high
        return row
    if not low:
        row["conductance_median"] = low
        return row

    row["conductance_median"] = mean([float(high), float(low)])
    return row


ION_SHORT_TO_LONG = {
    "K+": "potassium",
    "Ca2+": "calcium",
    "Na+": "sodium",
    "Ni2+": "nickel",
    "Cd2+": "cadmium",
    "Ba2+": "barium",
    "Sr2+": "strontium",
    "Li+": "lithium",
    "Zn2+": "zinc",
    "Rb+": "rubidium",
    "Cs+": "cesium",
    "Mn2+": "manganese",
    "Mg2+": "magnesium",
    "Cl-": "chlorine",
    "NH4+": "ammonia",
}

ION_ROW_TEMPLATE = {
    "ensg": None,
    "relative_cesium_conductance": None,
    "absolute_cesium_conductance": None,
    "relative_potassium_conductance": None,
    "absolute_potassium_conductance": None,
    "relative_sodium_conductance": None,
    "absolute_sodium_conductance": None,
    "relative_calcium_conductance": None,
    "absolute_calcium_conductance": None,
    "relative_lithium_conductance": None,
    "absolute_lithium_conductance": None,
    "relative_rubidium_conductance": None,
    "absolute_rubidium_conductance": None,
    "relative_magnesium_conductance": None,
    "absolute_magnesium_conductance": None,
    "relative_ammonia_conductance": None,
    "absolute_ammonia_conductance": None,
    "relative_barium_conductance": None,
    "absolute_barium_conductance": None,
    "relative_zinc_conductance": None,
    "absolute_zinc_conductance": None,
    "relative_manganese_conductance": None,
    "absolute_manganese_conductance": None,
    "relative_strontium_conductance": None,
    "absolute_strontium_conductance": None,
    "relative_cadmium_conductance": None,
    "absolute_cadmium_conductance": None,
    "relative_nickel_conductance": None,
    "absolute_nickel_conductance": None,
    "relative_chlorine_conductance": None,
    "absolute_chlorine_conductance": None,
}


def elongate_bool(code: str) -> bool:
    return True if code == "t" else False


def elongate_ion(short_ion: str) -> str:
    return ION_SHORT_TO_LONG[short_ion]


def insert_or_average(original, ion, hidden, conductance):
    assert ion in ION_SHORT_TO_LONG.values(), f"Invalid ion: {ion}."

    level = "relative" if hidden else "absolute"

    if original[f"{level}_{ion}_conductance"]:
        # There is a value in the original data
        log.warn(f"Had to average ion {ion} for gene {original['ensg']}")
        original[f"{level}_{ion}_conductance"] = mean(
            (original[f"{level}_{ion}_conductance"], conductance)
        )
    else:
        original[f"{level}_{ion}_conductance"] = conductance

    if level == "absolute":
        # We need to run this also for the relative slot
        original = insert_or_average(
            original, ion=ion, hidden=True, conductance=conductance
        )

    return original


def calculate_relative_conductances(original: dict) -> dict:
    denominator = -inf
    for key, item in original.items():
        if key.startswith("absolute") and item is not None:
            denominator = max(denominator, item)

    if denominator < 0:
        for key, item in original.items():
            if key.startswith("relative") and item is not None:
                denominator = max(denominator, item)

    assert denominator > 0

    # Bad idea to edit what you're iterating on
    itercopy = deepcopy(original)
    for key, item in itercopy.items():
        if key.startswith("relative") and item is not None:
            original[key] = item / denominator

    return original


def get_ion_channels_transaction(iuphar_data, iuphar_compiled, hugo):
    log.info("Finding ion channels in TCDB...")

    selectivity: pd.DataFrame = iuphar_data["selectivity"]

    log.info("Purging human-incompatible conductance data...")
    # 1 > human, 2 > mouse, 3 > rat, 20 > monkey, 18 > gorilla
    selectivity = selectivity.loc[
        selectivity["species_id"].isin(["1", "2", "3", "20", "18"])
    ]

    log.info("Calculating pseudo-median conductance values...")

    selectivity = selectivity.apply(calc_pseudo_mean, axis=1).dropna(how="all")

    sanity_check(
        not any(selectivity["conductance_median"].isna()),
        "Median conductance is not null",
    )

    # Drop the useless cols...
    selectivity = selectivity.drop(columns=["conductance_high", "conductance_low"])

    log.info("Returning to ensembl gene IDs...")
    database_links = iuphar_data["database_link"]
    # This drops everything not from ensembl
    database_links = database_links.loc[database_links["database_id"] == "15"]
    # We now select just human data
    database_links = database_links.loc[database_links["species_id"] == "1"]
    # Recast the frame...
    database_links = recast(
        database_links, {"placeholder": "ensg", "object_id": "object_id"}
    )

    # Merge, keeping all selectivity rows, dropping the others...
    selectivity = selectivity.merge(database_links, how="left", on="object_id")

    log.info("Dropping entries for which ENSG annotations are not available...")
    selectivity = selectivity.dropna(subset=("ensg"))

    log.info("Dropping useless columns...")
    selectivity = selectivity.drop(
        columns=["object_id", "selectivity_id", "species_id"]
    )

    conductances = []
    log.info("Populating absolute conductance values...")
    for gene in set(selectivity["ensg"]):
        conductance = deepcopy(ION_ROW_TEMPLATE)
        conductance["ensg"] = gene
        for _, row in selectivity.loc[selectivity["ensg"] == gene].iterrows():
            # A row has: id, ion, conductance_median, hide_conductance, ensg
            conductance = insert_or_average(
                conductance,
                ion=elongate_ion(row["ion"]),
                hidden=elongate_bool(row["hide_conductance"]),
                conductance=float(row["conductance_median"]),
            )

        conductances.append(calculate_relative_conductances(conductance))

    conductances = pd.DataFrame(conductances)

    log.info("Extending list with HGNC ion_channels...")
    hugo_channels = recast(
        hugo["ion_channels"], {"Ensembl gene ID": "ensg"}
    ).drop_duplicates()

    log.info("Removing porins...")
    porins = recast(hugo["porins"], {"Ensembl gene ID": "ensg"})
    original_len = len(hugo_channels)
    hugo_channels = hugo_channels[~hugo_channels["ensg"].isin(porins["ensg"])]

    sanity_check(len(hugo_channels) < original_len, "Porins were dropped successfully")

    sanity_check(
        all(conductances["ensg"].isin(hugo_channels["ensg"])),
        "All the IUPHAR channels are in the HUGO list.",
    )

    conductances = conductances.merge(hugo_channels, how="outer", on="ensg")

    sanity_check(conductances["ensg"].is_unique, "All conductance ENSGs are unique.")
    sanity_check(
        all(hugo_channels["ensg"].isin(conductances["ensg"])),
        "All Ensgs from HUGO were added.",
    )

    log.info("Using conductances to populate table...")
    ions = {
        "cesium": "Cs+",
        "potassium": "K+",
        "sodium": "Na+",
        "calcium": "Ca2+",
        "lithium": "Li+",
        "rubidium": "Rb+",
        "magnesium": "Mg2+",
        "ammonia": "NH4+",
        "barium": "Ba2+",
        "zinc": "Zn2+",
        "manganese": "Mg2+",
        "strontium": "Sr2+",
        "cadmium": "Cd2+",
        "nickel": "Ni2+",
        "chlorine": "Cl-",
    }
    hgnc_groups = {
        "sodium": "sodium_ion_channels",
        "calcium": "calcium_ion_channels",
        "potassium": "potassium_ion_channels",
        "chlorine": "chloride_ion_channels",
    }

    # For safety, i reset the index here
    conductances = conductances.reset_index()
    table = []
    for type, ion in ions.items():
        log.debug(f"Populating for {type}")
        # We just need to subset for the relative cond., as if the absolute is
        # available we have the relative  cond. for sure
        permeable = conductances["ensg"][
            conductances[f"relative_{type}_conductance"].notna()
        ]
        if type in hgnc_groups:
            hugo_permeable = recast(
                hugo[hgnc_groups[type]], {"Ensembl gene ID": "ensg"}
            )["ensg"]
            permeable = pd.concat(
                [permeable, hugo_permeable], axis=0, ignore_index=True
            )

        # In permeable we now have all the genes permeable for the type
        for gene in permeable:
            index = conductances.index[conductances["ensg"] == gene]
            if index.empty:
                log.warn(f"Failed to get index for gene {gene}")
                continue
            entry = {
                "ensg": gene,
                "carried_solute": ion,
                "relative_conductance": conductances.loc[
                    index, f"relative_{type}_conductance"
                ].iloc[0],
                "absolute_conductance": conductances.loc[
                    index, f"absolute_{type}_conductance"
                ].iloc[0],
            }
            table.append(entry)

    table = pd.DataFrame(table)
    # Add the ensgs with no conductance info back in
    table = table.merge(conductances["ensg"], how="outer", on="ensg")

    sanity_check(
        all(hugo_channels["ensg"].isin(table["ensg"])),
        "All Ensgs from HUGO were added.",
    )

    sanity_check(
        all(conductances["ensg"].isin(table["ensg"])),
        "All genes were ported to the new table",
    )

    log.info("Setting channel types...")
    gating_groups = {
        "voltage": recast(
            hugo["voltage_gated_ion_channels"], {"Ensembl gene ID": "ensg"}
        ).drop_duplicates(),
        "ligand": recast(
            hugo["ligand_gated_ion_channels"], {"Ensembl gene ID": "ensg"}
        ).drop_duplicates(),
        "pH": recast(
            hugo["ph_sensing_ion_channels"], {"Ensembl gene ID": "ensg"}
        ).drop_duplicates(),
        "stretch": recast(
            hugo["volume_regulated_ion_channels"], {"Ensembl gene ID": "ensg"}
        ),
    }

    # Fill the column with empty lists
    table["gating_mechanism"] = np.empty((len(table), 0)).tolist()

    # This raises warnings, but (I think that) they are false positives
    pd.set_option("mode.chained_assignment", None)
    for group, data in gating_groups.items():
        log.info(f"Populating '{group}' channels...")
        for ensg in data["ensg"]:
            table.loc[table["ensg"] == ensg, "gating_mechanism"].apply(
                lambda x: x.append(group)
            )
    pd.set_option("mode.chained_assignment", "warn")

    table = table.explode("gating_mechanism")
    log.warn("Impossible to annotate stretch-activated channels")
    log.warn("Impossible to know leakage channels")

    log.info("Adding IUPHAR ion channels back in...")
    # Add iuphar "ion_channel family"
    tf_table = iuphar_compiled["targets+families"]

    # The ion channels fall into either "lgic", "vgic" or "other_ic",
    # under the "type" column.
    tf_table = recast(tf_table, {"Type": "type", "Target id": "object_id"})

    # I re-use the "database links" frame to go from the IDs to ENSGs
    database_links["object_id"] = database_links["object_id"].astype(int)
    tf_table = tf_table.merge(database_links, how="left", on="object_id")

    tf_table = tf_table[tf_table["type"].isin(("lgic", "vgic", "other_ic"))]
    tf_table = tf_table.drop(columns=["type", "object_id"])

    table = table.merge(tf_table, how="outer", on="ensg")

    table = apply_thesaurus(table)
    return to_transaction(table, "channels")
