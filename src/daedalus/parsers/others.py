import logging

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
