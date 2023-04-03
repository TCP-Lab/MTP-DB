import logging
import re
from copy import deepcopy
from math import inf
from statistics import mean
from typing import Iterable, Optional

import numpy as np
import pandas as pd
from daedalus.static_solute_hits import STATIC_HITS, Entry
from daedalus.utils import (
    apply_thesaurus,
    explode_on,
    flatten,
    get_local_data,
    lmap,
    recast,
    sanity_check,
    split_ensembl_ids,
    split_refseq_ids,
    split_tcdb_ids,
    to_transaction,
)

log = logging.getLogger(__name__)

## NOTE: I don't add docstrings for these functions as they are a bit redundant:
# Imagine that the typical docstring is "Parses the input data to digested data
# for the database".


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


def get_tcdb_ids_transaction(tcdb_data, mart_data):
    relevant_data = recast(
        tcdb_data["RefSeq_to_TC"], {"refseq_id": "refseq_protein_id", "tc_id": "tcid"}
    )

    split_ids = lmap(split_tcdb_ids, relevant_data["tcid"])
    tcdb_ids = pd.DataFrame(
        {
            "refseq_protein_id": lmap(
                lambda x: x.id,
                lmap(split_refseq_ids, relevant_data["refseq_protein_id"]),
            ),
            "tcid": lmap(lambda x: x.full, split_ids),
            "tcid_type": lmap(lambda x: x.type, split_ids),
            "tcid_subtype": lmap(lambda x: x.subtype, split_ids),
            "tcid_family": lmap(lambda x: x.family, split_ids),
            "tcid_subfamily": lmap(lambda x: x.subfamily, split_ids),
        }
    )

    ensp_to_refseq = recast(
        mart_data["IDs"],
        {"ensembl_peptide_id": "ensp", "refseq_peptide": "refseq_protein_id"},
    ).drop_duplicates()

    # Add in the enst, mapping it to the refseq IDs
    ## TODO:: check if this merge is OK!!!
    tcdb_ids = tcdb_ids.merge(ensp_to_refseq, on="refseq_protein_id", how="inner")
    tcdb_ids = tcdb_ids.drop(columns="refseq_protein_id")

    log.warn("Cannot populate tcid_superfamilies at this time.")

    tcdb_ids = tcdb_ids.drop_duplicates()

    return to_transaction(tcdb_ids, "tcdb_ids")


def get_tcdb_definitions_transactions(tcdb_data):
    transactions = []

    # They do not provide a download for types, but there are not many of them
    # I transcribed them manually from https://www.tcdb.org/browse.php
    # Today is the 14th of November, 2022
    log.warn("Inputting hard-coded tcid_types...")
    tcdb_types = pd.DataFrame(
        {
            "tcid_type": ("1", "2", "3", "4", "5", "8", "9"),
            "type_name": (
                "Channels/Pores",
                "Electrochemical Potential-driven Transporters",
                "Primary Active Transporters",
                "Group Translocators",
                "Transmembrane Electron Carriers",
                "Accessory Factors Involved in Transport",
                "Incompletely Characterized Transport Systems",
            ),
        }
    )

    transactions.append(to_transaction(tcdb_types, "tcdb_types"))

    # Identical reasoning as above. But this time, I have copy-pasted them.
    log.warn("Inputting hard-coded tcid_subtypes...")
    subtypes = {
        "1.A": "α-Type Channels",
        "1.B": "β-Barrel Porins",
        "1.C": "Pore-Forming Toxins (Proteins and Peptides)",
        "1.D": "Non-Ribosomally Synthesized Channels",
        "1.E": "Holins",
        "1.F": "Vesicle Fusion Pores",
        "1.G": "Viral Fusion Pores",
        "1.H": "Paracellular Channels",
        "1.I": "Membrane-bounded Channels",
        "1.J": "Virion Egress Pyramidal Apertures",
        "1.K": "Phage DNA Injection Channels",
        "1.L": "Tunneling Nanotubes, TNTs",
        "1.M": "Membrane Fusion-mediating Spanins",
        "1.N": "Cell Fusion Pores",
        "1.O": "Physical Force (Sonoporation/Electroporation/Voltage, etc.)-induced Pores",
        "1.P": "Non-Envelop Virus Penitration Complex: A complex of host cell proteins that allow non-envelop virus to penetrate the endoplasmic reticular membrane.",
        "1.Q": "Fungal Septal Pores",
        "1.R": "Membrane Contact Site (MCS) for Interorganellar Transport",
        "1.S": "Bacterial Micro/NanoCompartment Shell Protein Pores",
        "1.T": "The Endosomal Sorting Complexes Required for Transport (ESCRT)",
        "1.U": "Cell-Permeable Peptide (CPP)",
        "1.V": "Filamentous Cyanobacterial Septal Pores",
        "1.W": "Phage Portal Protein Subclass",
        "2.A": "Porters (uniporters, symporters, antiporters)",
        "2.B": "Non-ribosomally Synthesized Porters",
        "2.C": "Ion-gradient-driven energizers",
        "2.D": "Transcompartment Lipid Carrier",
        "3.A": "P-P-bond-hydrolysis-driven transporters",
        "3.B": "Decarboxylation-driven transporters",
        "3.C": "Methyltransfer-driven transporters",
        "3.D": "Oxidoreduction-driven transporters",
        "3.E": "Light absorption-driven transporters",
        "4.A": "Phosphotransfer-driven Group Translocators (PTS)",
        "4.B": "Nicotinamide ribonucleoside uptake transporters",
        "4.C": "Acyl CoA ligase-coupled transporters",
        "4.D": "Polysaccharide Synthase/Exporters",
        "4.E": "Vacuolar Polyphosphate Polymerase-catalyzed Group Translocators",
        "4.F": "Choline/EthanolaminePhosphotransferase 1 (CEPT1)",
        "4.G": "Integral Membrane Protease Peptide Release (IMP-PR Translocators)",
        "4.H": "Lysylphosphatidylglycerol Synthase/Flippases",
        "5.A": "Transmembrane 2-electron transfer carriers",
        "5.B": "Transmembrane 1-electron transfer carriers",
        "8.A": "Auxiliary transport proteins",
        "8.B": "Ribosomally synthesized protein/peptide toxins/agonists that target channels and carriers",
        "8.C": "Non-ribosomally synthesized toxins that target channels, carriers and pumps",
        "8.D": "Mimetic Membranes for Solubilizing Integral Membrane Proteins",
        "8.E": "Lipid-Protein Interactions That Influence Transport",
        "9.A": "Recognized transporters of unknown biochemical mechanism",
        "9.B": "Putative transport proteins",
        "9.C": "Functionally characterized transporters lacking identified sequences",
    }
    tcdb_subtypes = pd.DataFrame(
        {"tcid_subtype": list(subtypes.keys()), "subtype_name": list(subtypes.values())}
    )

    transactions.append(to_transaction(tcdb_subtypes, "tcdb_subtypes"))

    log.info("Parsing tc definitions...")
    tcdb_families = recast(
        tcdb_data["TC_definitions"],
        {"tc_id": "tcid_family", "definition": "family_name"},
    )
    # Check if the family is a superfamily based on his name
    tcdb_families["is_superfamily"] = lmap(
        lambda x: int("superfamily" in x.lower()), tcdb_families["family_name"]
    )

    transactions.append(to_transaction(tcdb_families, "tcdb_families"))

    return transactions


def get_cosmic_transaction(cosmic, mart_data):
    relevant_data = recast(
        cosmic["census"],
        {
            "Gene Symbol": "hugo_gene_symbol",
            "Hallmark": "is_hallmark",
            "Tumour Types(Germline)": "germline_tt",
            "Tumour Types(Somatic)": "somatic_tt",
        },
    )

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
        mart_data["hugo_symbols"],
        {"hgnc_symbol": "hugo_gene_symbol", "ensembl_gene_id_version": "ensg"},
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

    # merge
    parsed_db = parsed_db.merge(symbols, how="inner", on="hugo_gene_symbol")
    # the inner merge should be good enough - it seems that most symbols are OK

    assert all(parsed_db["ensg"].notnull()), "There are some missing ENSG values!"
    assert all(
        parsed_db["hugo_gene_symbol"].notnull()
    ), "There are some missing symbols!"

    parsed_db = parsed_db.drop(columns=["hugo_gene_symbol"])

    return to_transaction(parsed_db.drop_duplicates(), "cosmic_genes")


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
    thesaurus = get_local_data("thesaurus.csv")["original"].tolist()
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


def get_aquaporins_transaction(hugo):
    aquaporins = recast(hugo["porins"], {"Ensembl gene ID": "ensg"}).drop_duplicates()

    log.warn("Impossible to determine tissue of expression for aquaporins.")

    return to_transaction(aquaporins, "aquaporins")


def get_atp_driven_carriers_transaction(hugo, iuphar):
    data = recast(hugo["atpases"], {"Ensembl gene ID": "ensg"}).drop_duplicates()

    log.info("Dropping AAA - Atpases since they are not transporters...")
    p = len(data["ensg"])
    aaa_atpases = recast(hugo["AAA_atpases"], {"Ensembl gene ID": "ensg"})
    data = data.drop(data[data["ensg"].isin(aaa_atpases["ensg"])].index)
    log.info(f"Dropped {p - len(data['ensg'])} entries.")

    log.info("Adding local annotations")
    local = get_local_data("atp_driven_ABC_data.csv")

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


def get_abc_transporters_transaction(hugo, iuphar):
    data = recast(
        hugo["ABC_transporters"], {"Ensembl gene ID": "ensg"}
    ).drop_duplicates()

    log.info("Adding local annotations")
    local = get_local_data("atp_driven_ABC_data.csv")

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
