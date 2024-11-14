import logging
from copy import copy, deepcopy
from math import inf
from statistics import mean

import numpy as np
import pandas as pd

from daedalus.utils import (
    apply_thesaurus,
    is_identical,
    recast,
    sanity_check,
    to_transaction,
)

log = logging.getLogger(__name__)

## NOTE: I don't add docstrings for these functions as they are a bit redundant:
# Imagine that the typical docstring is "Parses the input data to digested data
# for the database".


def calc_pseudo_mean(row: pd.Series):
    """Calculate an ion's 'pseudo-mean' conductance if the median is not available.

    This takes the iuphar row with conductance information and then calculates
    this 'pseudo median' value, handling failure edge cases. See "returns".

    Args:
        row [pd.Series]: A series with at least the "conductance_high",
            "conductance_low" and "conductance_median" values.
    Returns:
        - If there is a median already, returns that;
        - If there is no info, logs a warning and returns None;
        - If there is only a high or a low conductance value, returns the
            value that is present;
        - If there are both, returns the mean value of the two.
    """
    high, low, median = row[
        ["conductance_high", "conductance_low", "conductance_median"]
    ]
    if median:
        row["conductance_median"] = float(row["conductance_median"])
        return row

    if not high and not low:
        log.warn(f"Found missing conductance data for object ID {row['object_id']}")
        return

    if not high:
        row["conductance_median"] = float(high)
        return row
    if not low:
        row["conductance_median"] = float(low)
        return row

    row["conductance_median"] = mean([float(high), float(low)])
    return row


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


def get_ion_channels_transaction(iuphar_data, iuphar_compiled, hugo, gene_ontology):
    log.info("Finding ion channels in TCDB...")

    selectivity: pd.DataFrame = iuphar_data["selectivity"]

    # 'selectivity' looks like this:
    #   selectivity_id object_id   ion conductance_high conductance_low conductance_median hide_conductance species_id
    # 0              1       378   Cs+             None            None                  1                t          1
    # 1              2       378    K+             None            None                  1                t          1
    # 2              3       378   Na+             None            None                  1                t          1
    # 3              4       378  Ca2+             None            None        0.620000005                t          1
    # 4              5       379   Li+             None            None                  4                t          1
    # 5              6       379   Cs+             None            None                  4                t          1
    # 6              7       379   Rb+             None            None                  4                t          1
    # 7              8       379   Na+             None            None                  3                t          1
    # 8              9       379  Ca2+             None            None                  2                t          1
    # 9             10       379  Mg2+             None            None                  1                t          1
    # It has a few problems:
    #   1. There is non-human data mixed with human data;
    #   2. We want to collapse the three 'high' / 'low' / 'median' values
    #      to just one, slightly more useful albeit imprecise, value;
    #   3. It only has object IDs instead of the ENSGs that we need in the final
    #      table.

    # >>> Address point 1
    # NOTE: this might be useless due to point 2
    log.info("Purging human-incompatible conductance data...")
    # 1 > human, 2 > mouse, 3 > rat, 20 > monkey, 18 > gorilla
    # NOTE: This once considered all the above species, but now only uses
    # human data. The idea behind the last decision was that more values would
    # be filled that way.
    selectivity = selectivity.loc[
        selectivity["species_id"].isin(["1", "2", "3", "20", "18"])
    ]

    # >>> Address point 2
    log.info("Calculating pseudo-median conductance values...")
    selectivity = selectivity.apply(calc_pseudo_mean, axis=1).dropna(how="all")
    sanity_check(
        not any(selectivity["conductance_median"].isna()),
        "Median conductance is not null",
    )
    # Drop the useless cols...
    selectivity = selectivity.drop(
        columns=["conductance_high", "conductance_low", "species_id"]
    )

    # >>> Address point 3
    log.info("Returning to ensembl gene IDs...")
    database_links = iuphar_data["database_link"]
    # This drops everything not from ensembl
    database_links = database_links.loc[database_links["database_id"] == "15"]
    # We now select just human data
    database_links = database_links.loc[database_links["species_id"] == "1"]
    # Recast the frame...
    database_links = recast(
        database_links, {"placeholder": "ensg", "object_id": "object_id"}
    ).dropna()
    selectivity = selectivity.merge(database_links, how="inner", on="object_id")
    # Inner merge, since we have no need for lines with no ENSGs.
    # Remove the cols that are now useless after the merge.
    selectivity = selectivity.drop(columns=["object_id", "selectivity_id"])

    # Drop missing datapoints
    selectivity = selectivity.dropna()

    # 'selectivity' now looks like this:
    #      ion conductance_median hide_conductance             ensg
    # 10    K+              210.0                f  ENSG00000156113
    # 11    K+                272                f  ENSG00000156113
    # 12    K+         9.19999981                f  ENSG00000105642
    # 13    K+         9.89999962                f  ENSG00000080709
    # 14    K+                9.5                f  ENSG00000080709
    # 15   Rb+        0.980000019                t  ENSG00000080709
    # 16   Cs+        0.319999993                t  ENSG00000080709
    # 17  NH4+        0.610000014                t  ENSG00000080709
    # 18   Cs+        0.170000002                t  ENSG00000143603
    # 19   Rb+        0.800000012                t  ENSG00000143603
    #
    # We now need to average the "conductance_median" if there are more than
    # one value per ion for the same gene.
    # (e.g. above, lines 10 and 11 would need to be averaged to 241)
    #
    # We also have the issue of the 'f'/'t' "hide_conductance". If true, the
    # values are not shown on the website. If false, they are.
    # I assume that this means a few things:
    # - If the value is visible, it is more likely that it is a confirmed datapoint;
    # - If the value is visible, people that browse the website will treat
    #   it at face value (i.e. that is the conductance of that ion)
    # - If the value is not visible, only a comparative representation is
    #   done by the website (i.e. Na+ > Cl-).
    #
    # For this reason, I do the following:
    # - Ions that are 'f' will have an 'absolute' and 'relative' conductance;
    # - Ions that are 't' will have a 'relative' conductance only;
    # - Ions that have both 't' and 'f' will use the 'f' value only.

    # This does exactly what specified above.
    def calculate_relative_conductances(frame: pd.DataFrame) -> pd.DataFrame:
        # First, get rid of ions with both t and f values
        for ion in set(frame["ion"]):
            if sum((frame["ion"] == ion).tolist()) == 1:
                continue
            log.debug(f"Dropping conflicting conductance for '{ion}'")
            # Delete the 't' row
            key = (frame["ion"] == ion) & (frame["hide_conductance"] == "t")
            frame = frame[~key]

        # We now have just one ion per row, it is just a matter of calculating
        # both abs and rel or just rel
        # I use the usual "grow a list with templates" approach
        max_conductance = max(frame["conductance_median"])
        new_df = []
        template = {
            "ion": None,
            "absolute_conductance": None,
            "relative_conductance": None,
        }
        for _, row in frame.iterrows():
            t = copy(template)
            t["ion"] = row["ion"]
            if row["hide_conductance"] == "f":
                t["absolute_conductance"] = row["conductance_median"]
                t["relative_conductance"] = row["conductance_median"] / max_conductance
            else:
                t["relative_conductance"] = row["conductance_median"] / max_conductance

            new_df.append(t)

        return pd.DataFrame(new_df)

    conductances = (
        selectivity
        # First, get rid of any duplicates that are easily removed
        .groupby(["ensg", "ion", "hide_conductance"])
        .aggregate({"conductance_median": mean})
        .reset_index()
        # We can now calculate the relative conductances
        .groupby(["ensg"])
        .apply(calculate_relative_conductances)
        .reset_index(level="ensg")
    )

    # >> The IUPHAR has less genes than the HGNC. We heed to add them back in
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
    sanity_check(
        all(hugo_channels["ensg"].isin(conductances["ensg"])),
        "All Ensgs from HUGO were added.",
    )

    # This is now less of a frame about conductances than about ion channels
    ion_channels: pd.DataFrame = recast(
        conductances,
        {
            "ensg": None,
            "ion": "carried_solute",
            "absolute_conductance": None,
            "relative_conductance": None,
        },
    )
    assert isinstance(ion_channels, pd.DataFrame), "Satisfy the type checker"
    del conductances

    # >> Currently, we know only the permeabilities of genes with a conductance.
    # This is severely limiting, so we need to add the info from the HGNC
    # regarding the main channel classes as permeability info.
    # Each gene falls into:
    # - It has no info (just the ensg);
    # - It has info on some ions, but not of one the HGNC knows about;
    # - It has info on the same ion as the HGNC
    #
    # The idea is to make a new frame with the permeabilities, then merge it in.

    log.info("Adding in HGNC permeability data...")
    hgnc_groups = {
        "sodium_ion_channels": "Na+",
        "calcium_ion_channels": "Ca2+",
        "potassium_ion_channels": "K+",
        "chloride_ion_channels": "Cl-",
    }

    for group, ion in hgnc_groups.items():
        data = hugo[group]
        data["carried_solute"] = ion

        data = recast(
            data, {"Ensembl gene ID": "ensg", "carried_solute": "carried_solute"}
        ).drop_duplicates()

        ion_channels = ion_channels.merge(
            data, on=["ensg", "carried_solute"], how="outer"
        )

    # We now have a frame like this:
    #     gene solute
    # 0  gene1    Na+
    # 1  gene1    Cl-
    # 2  gene2   <NA>
    # 3  gene2    Na+
    #
    # We need to drop lines like line 2 above, since line 3 exists.
    # I do this again by grouping and applying a function.

    def drop_useless_duplicates(frame: pd.DataFrame) -> pd.DataFrame:
        if frame.shape[0] > 1:
            # If there is just one row, we have nothing to do.
            # If there is more than one row, this must be because there is some
            # solute info. This means that any rows with NA as a solute must be
            # dropped (as there is at least one other col with non-NA values)
            frame = frame.dropna(subset="carried_solute")

        return frame.drop(columns="ensg")

    log.info("Dropping useless duplicates...")
    ion_channels = (
        ion_channels.groupby(["ensg"])
        .apply(drop_useless_duplicates)
        .reset_index(level="ensg")
    )

    log.info("Setting channel gating types...")
    # Get a list of ensgs to fill in
    # The stretch ones need to be compiled from both HGNC and GO
    print(gene_ontology["mechanosensitive_channels"])
    _stretch = list(set(
        recast(hugo["volume_regulated_ion_channels"], {"Ensembl gene ID": "ensg"})["ensg"].tolist() +
        gene_ontology["mechanosensitive_channels"]
    ))
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
        "stretch": pd.DataFrame({"ensg": _stretch}),
    }

    # Fill the column with empty lists, that we then grow and explode later
    ion_channels["gating_mechanism"] = np.empty((len(ion_channels), 0)).tolist()

    # This raises warnings, but (I think that) they are false positives
    pd.set_option("mode.chained_assignment", None)
    for group, data in gating_groups.items():
        log.info(f"Populating '{group}' channels...")
        for ensg in data["ensg"]:
            ion_channels.loc[ion_channels["ensg"] == ensg, "gating_mechanism"].apply(
                lambda x: x.append(group)
            )
    pd.set_option("mode.chained_assignment", "warn")

    ion_channels = ion_channels.explode("gating_mechanism")
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

    ion_channels = ion_channels.merge(tf_table, how="outer", on="ensg")

    ## >> We have to patch the leaky data from the HGNC and IUPHAR with GO
    ## data. See https://github.com/CMA-Lab/MTP-DB/issues/34
    # I first apply the thesaurus to convert from simple ions to the more
    # generic 'cation' and 'anion' + to standardize the IDs for the GO
    # pass
    ion_channels = apply_thesaurus(ion_channels)

    # The GO frames have ENSG (with no versions). This is a pretty brutal
    # approach to do this, but there is no time to think of something better
    log.info("Adding missing ion channels based on GO annotations")
    all_go_channels = gene_ontology["monoatomic_ion_channel"]
    new_channels = [x for x in all_go_channels if x not in ion_channels["ensg"].tolist()]
    log.info(f"There are {len(new_channels)} extra channels to add.")
    # There does not seem to be a good way to "extend" a single column with more
    # rows. So I need to make a mostly-empty frame here
    # I explicitly set the colnames just to be safe
    new_channels = pd.DataFrame(
        {"ensg": new_channels},
        columns=["ensg", "carried_solute", "relative_conductance", "gating_mechanism"]
    )
    ion_channels = pd.concat(
        [ion_channels, new_channels],
        ignore_index = True
    )

    log.info("Adding GO annotations to ion channel list")

    def add_go_annotations(frame: pd.DataFrame) -> pd.DataFrame:
        # This should be applied on a frame with grouped ENSGs
        # This means that all rows should have the same col values
        # with the exception of the "carried_solute" col and the conductances
        _id = frame.name

        template_row = dict.fromkeys(frame.columns)
        template_row["ensg"] = _id
        checks = {
            "monoatomic_anion_channel": "anion",
            "monoatomic_cation_channel": "cation",
            "chloride_ion_channels": "Cl-",
            "calcium_ion_channels": "Ca2+",
            "potassium_ion_channels": "K+",
            "proton_ion_channels": "H+",
            "sodium_ion_channels": "Na+",
        }
        for key, value in checks.items():
            if (_id in gene_ontology[key]) & (
                value not in frame["carried_solute"].to_list()
            ):
                # This is way too wordy for its own good.
                #log.debug(f"Added {value} for gene {_id} from GO.")
                x = copy(template_row)
                x["carried_solute"] = value
                x = pd.DataFrame(x, index=[0])
                frame = pd.concat([frame.loc[:], x], axis=0).reset_index(drop=True)

        # I have no idea why pd.concat drops the ensg col, but it does.
        # so I have to do this badness (since the ensg col should not be here)
        if "ensg" in frame.columns:
            frame = frame.drop(columns="ensg")
        return frame

    ion_channels = (
        ion_channels.groupby(["ensg"], group_keys=True)
        .apply(add_go_annotations)
        .reset_index(level="ensg")
    )

    log.info("Dropping useless duplicates - again...")
    ion_channels = (
        ion_channels.groupby(["ensg"])
        .apply(drop_useless_duplicates)
        .reset_index(level="ensg")
    )

    ion_channels = apply_thesaurus(ion_channels)
    return to_transaction(ion_channels, "channels")
