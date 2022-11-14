CREATE TABLE gene_ids (
    ensg_version TEXT NOT NULL, -- from biomart > IDs+desc > ensembl_gene_id_version
    ensg TEXT PRIMARY KEY, -- from biomart > IDs+desc > ensembl_gene_id_version
    ensg_version_leaf INT NOT NULL -- from biomart > IDs+desc > ensembl_gene_id_version
);

CREATE TABLE transcript_ids (
    ensg TEXT NOT NULL, -- from biomart > IDs+desc > ensembl_gene_id_version
    enst TEXT PRIMARY KEY, -- from biomart > IDs+desc > ensembl_transcript_id_version
    enst_version TEXT UNIQUE NOT NULL, -- same as enst
    enst_version_leaf INT NOT NULL, -- same as enst
    is_canonical_isoform INT NOT NULL -- bool
);

CREATE TABLE mrna_refseq (
    -- These cannot be unique, as some refseq IDs are missing
    enst TEXT NOT NULL, -- from biomart > IDs+desc > ensembl_transcript_id_version
    refseq_transcript_id TEXT -- from biomart > IDs+desc > refseq_mrna
    -- refseq_transcript_id_version INT -- MISSING?? No version for refseq?
    -- refseq_transcrpit_id_version_leaf INT -- See aboveref
);

-- There are more pdb_ids than ensts, as a single transcript can have multiple deposited structs
CREATE TABLE protein_ids (
    enst TEXT, -- from biomart > IDs > ensembl_transcript_id
    ensp TEXT, -- from biomart > IDs > ensembl_peptide_id
    pdb_id TEXT, -- from biomart > IDs+desc > pdb
    refseq_protein_id TEXT -- from biomart > IDs > refseq_peptide
);

CREATE TABLE gene_names (
    ensg TEXT, -- from biomart > IDs+desc > ensembl_gene_id_version
    hugo_gene_id TEXT, -- from biomart > hugo_symbols > hgnc_id
    hugo_gene_symbol TEXT, -- from biomart > hugo_symbols > hugo_gene symbol
    -- (double check with the description field below)
    hugo_gene_name TEXT, -- from biomart > IDs+desc > description
    gene_symbol_synonyms TEXT -- ???
);

CREATE TABLE iuphar_targets (
    ensg TEXT,
    target_id TEXT NOT NULL, -- unsure if this is unique UPDATE: it is not
    target_name TEXT NOT NULL, --
    family_id INT NOT NULL,
    family_name TEXT NOT NULL
    -- Add an "aliases" col with the 'target systematic' + 'target abbreviated' cols
);

CREATE TABLE iuphar_ligands (
    ligand_id TEXT PRIMARY KEY, -- Ligand ID
    ligand_type TEXT NOT NULL, -- Type
    ligand_name TEXT NOT NULL, -- Name
    ensembl_id INT, -- Ensembl ID (this has non-human proteins)
    pubchem_sid INT, -- PubChem SID
    pubchem_cid INT, -- PubChem CID
    is_approved_drug INT, -- Approved
    is_withdrawn_drug INT -- Withdrawn
);

CREATE TABLE iuphar_interaction (
    -- Filter the csv to just human stuff
    target_id INT, -- Target ID (why not null?)
    ligand_id INT NOT NULL, -- Ligand ID
    is_approved_drug INT, -- Approved
    ligand_action TEXT, -- Action
    ligand_selectivity TEXT, -- Selectivity
    is_endogenous INT, -- Endogenous
    is_primary_target INT -- Primary Target
);

CREATE TABLE tcdb_ids (
    ensp INT,
    tcid TEXT, -- e.g. 1.A.4.5.11
    tcid_type INT, -- e.g. 1
    tcid_subtype TEXT, -- e.g. 1.A
    tcid_family TEXT, -- e.g. 1.A.4
    tcid_subfamily TEXT, -- e.g. 1.A.4.5
    tcid_superfamily TEXT -- e.g. 1.A.4 - but only the superfamily
);

CREATE TABLE tcdb_types (
    tcid_type INT,
    type_name TEXT
);

CREATE TABLE tcdb_subtypes (
    tcid_subtype TEXT,
    subtype_name TEXT
);

-- This is from tcdb_TC_definitions.csv
CREATE TABLE tcdb_families (
    tcid_family TEXT PRIMARY KEY,
    family_name TEXT,
    -- There are only family IDs, and some are considered superfamilies,
    -- so we can just store if the family is, in reality, a superfamily
    is_superfamily INT -- bool
);

CREATE TABLE gene_ontology_description (
    term TEXT PRIMARY KEY,
    term_name TEXT,
    go_namespace TEXT,
    definition TEXT
);

CREATE TABLE transcript_gene_ontology (
    term TEXT,
    enst TEXT
);

----- NOVEL DATA ------
-- "Channels" are all
CREATE TABLE channels (
    enst INT PRIMARY KEY,
    -- How do we represent conductance?
    conductance TEXT,
    -- selectivity
    is_calcium_permeable INT,
    is_potassium_permeable INT,
    is_chlorine_permeable INT,
    is_iron_permeable INT,
    is_phosphate_permeable INT,
    is_magnesium_permeable INT,
    is_chromium_permeable INT,
    is_copper_permeable INT,
    is_zinc_permeable INT,
    is_iodine_permeable INT,
    is_bicarbonate_permeable INT,
    is_proton_permeable INT,
    -- general selectivity
    is_cation_permeable INT,
    is_anion_permeable INT,
    -- gating
    gating_mechanism TEXT,
    voltage_threshold_coefficient INT
);

CREATE TABLE carriers (
    enst INT PRIMARY KEY,
    class TEXT, -- symport, antiport, ...
    -- transport_type "passive", "primary", "secondary"
    is_secondary INT, -- bool, uses secondary energy?
    to_lumen_pubchem_id TEXT, -- pubchem IDs of molecules carried to the lumen
    to_exterior_pubchem_id TEXT,
    rate_coefficient TEXT, -- trasport carry rate, like 1/2 Vmax
    rate_maximum TEXT -- Vmax
);
