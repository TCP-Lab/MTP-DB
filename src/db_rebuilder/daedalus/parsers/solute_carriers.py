import logging
import re
from typing import Optional

import numpy as np
import pandas as pd
from daedalus.static_solute_hits import STATIC_HITS, Entry
from daedalus.utils import (
    apply_thesaurus,
    flatten,
    get_local_csv,
    lmap,
    recast,
    to_transaction,
)

log = logging.getLogger(__name__)

## NOTE: I don't add docstrings for these functions as they are a bit redundant:
# Imagine that the typical docstring is "Parses the input data to digested data
# for the database".


PAR_RE = re.compile(r"(\(.*?\))")
BRA_RE = re.compile(r"(\[.*?\])")


def purge_data_in_parenthesis(string: str) -> str:
    ci_matches = PAR_RE.search(string)
    if ci_matches:
        for match in ci_matches.groups():
            string = string.replace(match, "").strip()

    sq_matches = BRA_RE.search(string)
    if sq_matches:
        for match in sq_matches.groups():
            string = string.replace(match, "").strip()

    if sq_matches is None and ci_matches is None:
        return string

    return purge_data_in_parenthesis(string)


SLC_CARRIER_TYPES = {"C": "symport", "E": "antiporter", "F": "uniporter", "O": None}


def extract_slc_carrier_type(tokens: set[str]) -> Optional[str]:
    ## >>> BIG FAT WARNING <<<
    # This is very experimental and very rough. It does not cover all edge cases,
    # but works fairly well for most entries. But it needs manual tweakage.
    if not isinstance(tokens, set):
        return None

    slc_type = None
    for key, value in SLC_CARRIER_TYPES.items():
        if key in tokens and slc_type is None:
            slc_type = value
        elif key in tokens and slc_type is not None:
            log.warn(f"Got conflicting types ({tokens}). Returning NA")
            return None

    return slc_type


def purge_carrier_types(tokens: set[str]):
    if not isinstance(tokens, set):
        return None

    for tk in SLC_CARRIER_TYPES.keys():
        if tk in tokens:
            tokens.remove(tk)

    return tokens


def tokenize_slc(string: str):
    if not isinstance(string, str):
        return np.NaN
    # The spaces are important around and and or
    tokens = ("/", ",", ";", " and ", " or ")
    string = purge_data_in_parenthesis(string)
    assert "(" not in string, f"Purging did not work on {string}"
    assert ")" not in string, f"Purging did not work on {string}"

    string = [string]
    for tk in tokens:
        string = [y for x in string for y in x.split(tk)]
        # I strip later to preserve stuff like ' and ' and ' or '

    return set([x.strip() for x in string])


def warn_long_solutes(string, possibilities):
    if isinstance(string, str) and string not in possibilities:
        log.warn(f"Found an unusually long solute: '{string}'")


def explode_slc(data: pd.DataFrame) -> pd.DataFrame:
    """Explode the solute carriers data.

    The slc downloaded has comma-delimited data, and it is mixed with
    info about the carrier type. This explodes the data and reorders it.

    Let's hope that there is no "F" solute.

    Expects a df with "driving" col with driving forces + transporter types,
    and "solute" col with solutes.
    """
    # Fuse together the data
    log.info("Fusing carrier information...")
    data["exploded_solute"] = [
        tokenize_slc(f"{x},{y}") for x, y in zip(data["solutes"], data["driving"])
    ]
    log.info("Extracting carrier types")
    data["port_type"] = [extract_slc_carrier_type(x) for x in data["exploded_solute"]]
    log.info("Setting carrier solutes...")
    data["exploded_solute"] = data["exploded_solute"].apply(purge_carrier_types)

    log.info("Exploding slc...")
    data = data.drop(columns=["solutes", "driving"])
    data = data.explode("exploded_solute")

    log.info("Removing NA-like terms...")
    to_remove = [
        "possibly proton-linked",
        "Uncertain",
        "+",  # This is just plain wrong
        "?Ch",
        "H+ ?",
        "polyamines?",  # Are you sure about that?
        "probably organic anions",
        "E?",
        "not specific",
        "inconclusive",
        "glycine ?",
        "C ?",
        "nan",
        "?",  # Just ?
        "",
    ]
    data.loc[
        [x in to_remove for x in data["exploded_solute"].tolist()], "exploded_solute"
    ] = pd.NA

    log.info("Checking possible anomalies...")
    # I use the thesaurus + a manual list for approved symbols
    thesaurus = get_local_csv("thesaurus.csv")["original"].tolist()
    data["exploded_solute"].apply(warn_long_solutes, possibilities=thesaurus)

    solutes = data["exploded_solute"].dropna().tolist()
    solutes = [x for x in solutes if x not in thesaurus]
    print("\n".join(set(solutes)))

    return data


EQUIVALENCE = {"1Na+:1HCO3-(out)or1Na:CO32*": "1Na+:2/3HCO3-(out)or1Na+:CO32*"}
SOLUTE_FINDER = re.compile(r"^([0-9]{0,2})(.+?)([0-9]?[+\-\*]?)(?:\((in|out)\))?$")
PAR_REMOVER = re.compile(r"\(.*?\)")
TAG_RE = re.compile(r"<.+?>")
PROB_RE = re.compile(r"Probably")


def charge_to_int(charge: str) -> int:
    if not charge:
        return 0
    if charge == "+":
        return 1
    if charge == "-":
        return -1

    if "+" in charge:
        try:
            value = int(charge[:-1])
        except ValueError:
            log.error(f"Cannot parse charge {charge}. Returning 1")
            return 1
        return value

    if "-" in charge:
        try:
            value = int(charge[:-1])
        except ValueError:
            log.error(f"Cannot parse charge {charge}. Returning -1")
            return -1
        return -value

    raise ValueError(f"Cannot parse charge {charge}")


def calculate_charge_balance(
    charge_in: int, charge_in_n: int, charge_out: int, charge_out_n: int
):
    # Canonically, "in" charges are negative.
    # Thus, a "-" that enters is +1, and a "+" that enters is "-1"
    # A "+" that exits in +1, and a "-" that exits is -1.
    # So it's outward - inward
    return charge_out * charge_out_n - charge_in * charge_in_n


def grac_to_entry(id: int, grac: str) -> Optional[Entry]:
    # Prefiltering
    if not isinstance(grac, str):
        return None

    if "Unknown" in grac:
        return None

    grac = grac.replace(" ", "")
    grac = re.sub(TAG_RE, "", grac)  # Remove tags
    grac = re.sub(PROB_RE, "", grac)  # Remove "Probably"
    grac = grac.rstrip(".")  # Some entries end with a .
    if grac in STATIC_HITS:
        hit = STATIC_HITS[grac]
        if hit is None:
            return None
        with_id = []
        for item in hit:
            # Add IDs to the hit
            item.id = id
            with_id.append(item)
        return with_id

    if ";" in grac:
        split = grac.split(";")
        res = []
        for i, item in enumerate(split, 1):
            parsed = grac_to_entry(id, item)
            if not parsed:
                continue

            if isinstance(parsed, list):
                parsed = list(map(lambda x: setattr(x, "mode", i), parsed))
                res.extend(parsed)

            res.append(parsed)
        return res

    # This is not an edge case. This means that it is a two-long split
    split = grac.split(":")
    if len(split) != 2:
        log.warning(
            f"The string {grac} did not split correctly. Returning None for ID {id}"
        )
        return None

    match1 = SOLUTE_FINDER.match(split[0]).groups()
    match2 = SOLUTE_FINDER.match(split[1]).groups()

    # The solute should not have anything in ()
    # They are usually extra info (not caught by the in/out filters)
    # that should be removed.
    solute1 = PAR_REMOVER.sub("", match1[1])
    solute2 = PAR_REMOVER.sub("", match2[1])

    # Match:
    # Position 0: the number of solutes
    # Position 1: the solute itself
    # Position 2: the charge
    # Position 3: the direction

    log.debug(
        f"Solute: {split} >> n: {match1[0]}, {solute1}{match1[2]}, charge {match1[2]}, direction {match1[3]}"
    )
    log.debug(
        f"Solute: {split} >> n: {match2[0]}, {solute2}{match2[2]}, charge {match2[2]}, direction {match2[3]}"
    )

    # If we have info on the charges, the n-s and the direction of the flux, we can
    # calculate the charge inbalance
    # We always have "match[1]", so we can just run all
    net_charge = False  # A default
    if all(match1) and all(match2):
        # There can be a charge inbalance, as we have info on a
        if match1[3] == "in":
            # Match 1 is inward
            net_charge = calculate_charge_balance(
                charge_in=charge_to_int(match1[2]),
                charge_in_n=int(match1[0]),
                charge_out=charge_to_int(match2[2]),
                charge_out_n=int(match2[0]),
            )
        else:
            net_charge = calculate_charge_balance(
                charge_out=charge_to_int(match1[2]),
                charge_out_n=int(match1[0]),
                charge_in=charge_to_int(match2[2]),
                charge_in_n=int(match2[0]),
            )
        log.debug(f"Detected possible charge imbalance. Net charge {net_charge}")

    return [
        Entry(
            id=id,
            net_charge=net_charge,
            carried_solute=solute1,
            direction=match1[3] or None,
            stoichiometry=int(match1[0]) if match1[0] else None,
        ),
        Entry(
            id=id,
            net_charge=net_charge,
            carried_solute=solute2,
            direction=match2[3],
            stoichiometry=int(match2[0]) if match2[0] else None,
        ),
    ]


def get_solute_carriers_transaction(hugo, iuphar, slc):
    log.info("Recasting solute carrier frames...")
    solute_carriers = recast(
        hugo["solute_carriers"],
        {"Ensembl gene ID": "ensg", "Approved symbol": "hugo_symbol"},
    ).drop_duplicates()

    stoich: pd.DataFrame = (
        recast(
            iuphar["transporter"],
            {
                "object_id": "object_id",
                "grac_stoichiometry": "stoichiometry_annotations",
            },
        )
        .drop_duplicates()
        .dropna(subset="stoichiometry_annotations")
    )

    object_infos = recast(
        iuphar["database_link"],
        {
            "object_id": "object_id",
            "database_id": "db",  # n. 15 is ensg,
            "placeholder": "ensg",
        },
    )

    slc = recast(
        slc,
        {
            "SLC name": "hugo_symbol",
            "Transport type*": "driving",
            "Substrates": "solutes",
        },
    )

    object_infos: pd.DataFrame = object_infos.loc[object_infos["db"] == "15",]
    object_infos = object_infos.drop(columns="db")
    # Drop the non-human IDs
    object_infos = object_infos.loc[
        lmap(lambda x: x.startswith("ENSG"), object_infos["ensg"]),
    ]

    # Merge with stochiometry info
    stoich = stoich.merge(object_infos, how="left", on="object_id")

    # The first here is the row_id
    # The first in the tuple is the object id
    # We don't need them
    log.info("Parsing stoichiometry information from IuPhar...")
    entries = []
    for _, (_, grac, ensg) in stoich.iterrows():
        entry = grac_to_entry(ensg, grac)
        if entry and not entry == [None]:
            entries.append(entry)

    # Convert to dicts
    entries = flatten(entries)
    entries = filter(lambda x: x is not None, entries)
    entries = map(lambda x: x.__dict__, entries)
    stoich_info = pd.DataFrame(entries)

    # This makes (for some reason) duplicated rows. Drop them
    stoich_info = stoich_info.drop_duplicates()

    # We now need to merge the various dataframes:
    # - solute_carriers has all the ENSGs of the soluter carriers
    # - stoich_info has the info on the stoichiometry;
    # - slc has the transportes types + extra solutes that the iuphar does not have
    log.info("Populating transported solutes...")
    solute_carriers = solute_carriers.merge(
        stoich_info, left_on="ensg", right_on="id", how="left"
    ).drop(columns="id")

    solute_carriers = solute_carriers.merge(slc, on="hugo_symbol", how="left")

    solute_carriers = explode_slc(solute_carriers)

    solute_carriers = solute_carriers.drop(
        columns=["hugo_symbol", "exploded_solute"]
    ).drop_duplicates()

    solute_carriers = apply_thesaurus(solute_carriers)

    return to_transaction(solute_carriers, "solute_carriers")
