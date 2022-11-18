import logging

import pandas as pd
from daedalus.utils import (
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


def get_go_transactions(mart_data):
    log.info("Extracting terms...")
    transactions = []

    data = recast(
        mart_data["GO_transcripts"],
        {
            "ensembl_transcript_id": "enst",
            "go_id": "term",
        },
    ).drop_duplicates()
    transactions.append(to_transaction(data, "transcript_gene_ontology"))

    data = recast(
        mart_data["GO_definitions"],
        {
            "go_id": "term",
            "name_1006": "term_name",
            "namespace_1003": "go_namespace",
            "definition_1006": "definition",
        },
    ).drop_duplicates()
    transactions.append(to_transaction(data, "gene_ontology_description"))

    return transactions
