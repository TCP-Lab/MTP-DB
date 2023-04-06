import logging

import pandas as pd
from daedalus.utils import (
    lmap,
    recast,
    split_refseq_ids,
    split_tcdb_ids,
    to_transaction,
)

log = logging.getLogger(__name__)

## NOTE: I don't add docstrings for these functions as they are a bit redundant:
# Imagine that the typical docstring is "Parses the input data to digested data
# for the database".


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
