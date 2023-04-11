import logging
from copy import deepcopy

import pandas as pd
from daedalus.utils import lmap, recast, sanity_check, split_ensembl_ids, to_transaction

log = logging.getLogger(__name__)

## NOTE: I don't add docstrings for these functions as they are a bit redundant:
# Imagine that the typical docstring is "Parses the input data to digested data
# for the database".


def get_cosmic_transaction(cosmic, mart_data):
    # The data is essentially all there, we just need to change its form to
    # be added in the DB as I want it to.
    relevant_data = recast(
        cosmic["census"],
        {
            "Gene Symbol": "hugo_gene_symbol",
            "Hallmark": "is_hallmark",
            "Tumour Types(Germline)": "germline_tt",
            "Tumour Types(Somatic)": "somatic_tt",
        },
    )

    # I make the new frame line-by-line, by filling in a template row
    new_db_data = []
    template = {
        "hugo_gene_symbol": None,
        "is_hallmark": None,
        "is_somatic": None,
        "is_germline": None,
        "tumor_type": None,
    }
    for _, row in relevant_data.iterrows():
        temp = deepcopy(template)

        temp["hugo_gene_symbol"] = row["hugo_gene_symbol"]
        temp["is_hallmark"] = str(row["is_hallmark"]) == "Yes"

        somatic_tts = str(row["somatic_tt"]).split(", ") or []
        germline_tts = str(row["germline_tt"]).split(", ") or []

        somatic_tts = [x for x in somatic_tts if x != "nan"]
        germline_tts = [x for x in germline_tts if x != "nan"]

        all_tts = []
        all_tts.extend(somatic_tts)
        all_tts.extend(germline_tts)

        assert len(all_tts) > 0

        for tumor_type in all_tts:
            temp_copy = deepcopy(temp)

            temp_copy["tumor_type"] = tumor_type
            temp_copy["is_somatic"] = tumor_type in somatic_tts
            temp_copy["is_germline"] = tumor_type in germline_tts
            new_db_data.append(temp_copy)

    parsed_db = pd.DataFrame(new_db_data)

    # Move from hugo symbols to ensg
    symbols = recast(
        mart_data["gene_names"],
        {"hgnc_symbol": "hugo_gene_symbol", "gene_stable_id_version": "ensg"},
    )
    # purge the version
    symbols = pd.DataFrame(
        {
            "hugo_gene_symbol": symbols["hugo_gene_symbol"],
            "ensg": lmap(
                lambda x: split_ensembl_ids(x).full_id_no_version, symbols["ensg"]
            ),
        }
    )

    parsed_db = parsed_db.merge(symbols, how="inner", on="hugo_gene_symbol")
    # the inner merge should be good enough - it seems that most symbols are OK

    sanity_check(
        all(parsed_db["ensg"].notnull()), "There are some missing ENSG values!"
    )
    sanity_check(
        all(parsed_db["hugo_gene_symbol"].notnull()), "There are some missing symbols!"
    )

    # We don't need the gene symbols anymore
    parsed_db = parsed_db.drop(columns=["hugo_gene_symbol"])

    return to_transaction(parsed_db.drop_duplicates(), "cosmic_genes")
