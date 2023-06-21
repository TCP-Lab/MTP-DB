import logging

import pandas as pd

from daedalus.utils import recast, to_transaction

log = logging.getLogger(__name__)

## NOTE: I don't add docstrings for these functions as they are a bit redundant:
# Imagine that the typical docstring is "Parses the input data to digested data
# for the database".


def get_aquaporins_transaction(hugo, patlas):
    aquaporins = recast(hugo["porins"], {"Ensembl gene ID": "ensg"}).drop_duplicates()

    tissue_expression = recast(
        patlas["normal_tissue_expression"],
        {
            "Gene": "ensg",
            "Tissue": "expression_tissue",
            "Level": "expression_level",
            "Reliability": "rel",
        },
    )

    # No need for 'Uncertain' stuff
    tissue_expression = tissue_expression[tissue_expression["rel"] != "Uncertain"]
    # No need for 'not expressed' entries
    tissue_expression = tissue_expression[
        tissue_expression["expression_level"] != "Not detected"
    ]
    # We don't need these anymore
    tissue_expression.drop(columns=["rel", "expression_level"], inplace=True)

    # Clean up the different expression tissues
    tissue_expression["expression_tissue"] = tissue_expression[
        "expression_tissue"
    ].apply(lambda x: x.strip("1234567890").strip())

    aquaporins = aquaporins.merge(tissue_expression, how="left", on="ensg")

    aquaporins.drop_duplicates()

    return to_transaction(aquaporins, "aquaporins")


def get_origin_transaction(patlas):
    # These are all simple recasts and selections to remove "uncertain" or
    # "no expression" samples.
    tissue_expression = recast(
        patlas["normal_tissue_expression"],
        {
            "Gene": "ensg",
            "Tissue": "tissue",
            "Cell type": "cell_type",
            "Level": "expression_level",
            "Reliability": "rel",
        },
    )
    subcellular = recast(
        patlas["subcellular_location"],
        {
            "Gene": "ensg",
            "Main location": "subcellular_location",
            "Reliability": "rel",
            "Extracellular location": "extracellular_location",
        },
    )

    # No need for 'Uncertain' stuff
    tissue_expression = tissue_expression[tissue_expression["rel"] != "Uncertain"]
    subcellular = subcellular[subcellular["rel"] != "Uncertain"]

    # No need for 'not expressed' entries
    tissue_expression = tissue_expression[
        tissue_expression["expression_level"] != "Not detected"
    ]

    # We don't need these anymore
    tissue_expression.drop(columns=["rel"], inplace=True)
    subcellular.drop(columns=["rel"], inplace=True)

    # Explode the 'location' column
    def spilt_subloc(x):
        if x:
            return str(x).split(";")
        return x

    subcellular["subcellular_location"] = subcellular["subcellular_location"].apply(
        spilt_subloc
    )
    subcellular = subcellular.explode(column=["subcellular_location"])

    # Clean up the different expression tissues
    tissue_expression["tissue"] = tissue_expression["tissue"].apply(
        lambda x: x.strip("1234567890").strip()
    )

    # We produce the final dataframe
    merged = tissue_expression.merge(subcellular, how="outer", on="ensg")

    merged = merged.drop_duplicates()

    return to_transaction(merged, "origin")


def get_function_transaction(iuphar):
    function = recast(
        iuphar["physiological_function"],
        {"object_id": None, "description": "physiological_function"},
    )
    # The IUPHAR has this dataframe with the functional annotations
    # We have to unpack them and merge
    log.info("Returning to ensembl gene IDs...")
    database_links = iuphar["database_link"]
    # This drops everything not from ensembl
    database_links = database_links.loc[database_links["database_id"] == "15"]
    # We now select just human data
    database_links = database_links.loc[database_links["species_id"] == "1"]
    # Recast the frame...
    database_links = recast(
        database_links, {"placeholder": "ensg", "object_id": None}
    ).dropna()

    function: pd.DataFrame = function.merge(database_links, on="object_id")
    function.drop(columns=["object_id"], inplace=True)

    # Now we have more or less what we want.

    function.dropna(inplace=True)

    function.drop_duplicates(inplace=True)

    return to_transaction(function, "function")


def get_structure_transaction(iuphar):
    structure = recast(
        iuphar["structural_info"],
        {
            "object_id": None,
            "species_id": None,
            "pore_loops": None,
            "transmembrane_domains": "membrane_passes",
        },
    )
    # Drop non-human data
    structure = structure[structure["species_id"] == "1"]

    # This bit is copy-pasted. Get the iuphar object-id to ensg frame
    log.info("Returning to ensembl gene IDs...")
    database_links = iuphar["database_link"]
    database_links = database_links.loc[database_links["database_id"] == "15"]
    database_links = database_links.loc[database_links["species_id"] == "1"]
    database_links = recast(
        database_links, {"placeholder": "ensg", "object_id": None}
    ).dropna()

    structure: pd.DataFrame = structure.merge(database_links, on="object_id")
    structure.drop(columns=["object_id", "species_id"], inplace=True)

    structure.dropna(subset=["membrane_passes", "pore_loops"], how="all", inplace=True)
    structure.drop_duplicates(inplace=True)

    return to_transaction(structure, "structure")
