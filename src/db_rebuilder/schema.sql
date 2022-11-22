CREATE TABLE gene_ids (
    ensg_version TEXT UNIQUE NOT NULL, -- from biomart > IDs+desc > ensembl_gene_id_version
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
    ensp TEXT NOT NULL,
    tcid TEXT NOT NULL, -- e.g. 1.A.4.5.11
    tcid_type INT NOT NULL, -- e.g. 1
    tcid_subtype TEXT NOT NULL, -- e.g. 1.A
    tcid_family TEXT NOT NULL, -- e.g. 1.A.4
    tcid_subfamily TEXT NOT NULL, -- e.g. 1.A.4.5
    tcid_superfamily TEXT -- NOT NULL (eventually) e.g. 1.A.4 - but only the superfamily
);

CREATE TABLE tcdb_types (
    tcid_type INT PRIMARY KEY,
    type_name TEXT UNIQUE NOT NULL
);

CREATE TABLE tcdb_subtypes (
    tcid_subtype TEXT PRIMARY KEY,
    subtype_name TEXT UNIQUE NOT NULL
);

-- This is from tcdb_TC_definitions.csv
CREATE TABLE tcdb_families (
    tcid_family TEXT PRIMARY KEY,
    family_name TEXT NOT NULL,
    -- There are only family IDs, and some are considered superfamilies,
    -- so we can just store if the family is, in reality, a superfamily
    is_superfamily INT NOT NULL -- bool
);


----- NOVEL DATA ------
-- "Channels" are all
CREATE TABLE channels (
    ensg INT PRIMARY KEY,
    relative_cesium_conductance REAL,
    absolute_cesium_conductance REAL,
    relative_potassium_conductance REAL,
    absolute_potassium_conductance REAL,
    relative_sodium_conductance REAL,
    absolute_sodium_conductance REAL,
    relative_calcium_conductance REAL,
    absolute_calcium_conductance REAL,
    relative_lithium_conductance REAL,
    absolute_lithium_conductance REAL,
    relative_rubidium_conductance REAL,
    absolute_rubidium_conductance REAL,
    relative_magnesium_conductance REAL,
    absolute_magnesium_conductance REAL,
    relative_ammonia_conductance REAL,
    absolute_ammonia_conductance REAL,
    relative_barium_conductance REAL,
    absolute_barium_conductance REAL,
    relative_zinc_conductance REAL,
    absolute_zinc_conductance REAL,
    relative_manganese_conductance REAL,
    absolute_manganese_conductance REAL,
    relative_strontium_conductance REAL,
    absolute_strontium_conductance REAL,
    relative_cadmium_conductance REAL,
    absolute_cadmium_conductance REAL,
    relative_nickel_conductance REAL,
    absolute_nickel_conductance REAL,
    relative_chlorine_conductance REAL,
    absolute_chlorine_conductance REAL,
    -- gating
    gating_mechanism TEXT,
    voltage_threshold_coefficient INT
);
