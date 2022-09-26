CREATE TABLE gene_ids (
    ensg INT PRIMARY KEY, 
    ensg_version_leaf INT NOT NULL,
    refseq_gene_id TEXT UNIQUE NOT NULL,
    refseq_gene_id_version INT NOT NULL,
    go_terms TEXT
);

CREATE TABLE transcript_ids (
    ensg INT NOT NULL,
    enst INT PRIMARY KEY,
    is_primary_transcript INT NOT NULL, -- bool
    pdb_id TEXT UNIQUE,
    refseq_protein_id TEXT UNIQUE NOT NULL
);

CREATE TABLE gene_names (
    ensg INT PRIMARY KEY,
    hugo_gene_symbol TEXT UNIQUE NOT NULL,
    hugo_gene_name TEXT NOT NULL,
    gene_symbol_synonyms TEXT
);

CREATE TABLE iuphar_ids (
    ensg INT PRIMARY KEY,
    target_id TEXT UNIQUE NOT NULL, -- unsure if this is unique
    target_name TEXT NOT NULL,
    family_id INT NOT NULL, 
    family_name TEXT NOT NULL
);

CREATE TABLE iuphar_ligands (
    ligand_id TEXT PRIMARY KEY,
    is_proteic INT NOT NULL, -- Bool
    ensg INT UNIQUE, -- If is_proteic 
    gene_symbol TEXT, -- If is_proteic
    pubchem_sid INT, -- If not is_proteic,
    is_endogenous INT, -- bool
    name TEXT NOT NULL
);

CREATE TABLE iuphar_interaction (
    interaction_id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL,
    ligand_id TEXT NOT NULL,
    is_approved_drug INT NOT NULL, -- bool
    interaction_type TEXT NOT NULL,
    ligand_action TEXT,
    ligand_action_extras TEXT,
    ligand_selectivity TEXT,
    is_primary_target INT, -- bool
    receptor_site TEXT,
    ligand_context TEXT
);

CREATE TABLE tcdb_ids (
    enst INT PRIMARY KEY,
    tcid TEXT UNIQUE, -- e.g. 1.A.4.5.11
    tcid_type INT, -- e.g. 1
    tcid_subtype TEXT, -- e.g. 1.A
    tcid_family TEXT, -- e.g. 1.A.4
    tcid_subfamily TEXT -- e.g. 1.A.4.5
);

CREATE TABLE tcdb_subfamily (
    tcid_subfamily TEXT PRIMARY KEY,
    subfamily_name TEXT
);

CREATE TABLE tcdb_families (
    tcid_family TEXT PRIMARY KEY,
    family_name TEXT,
    -- There are only family IDs, and some are considered superfamilies,
    -- so we can just store if the family is, in reality, a superfamily
    is_superfamily INT -- bool
);

CREATE TABLE gene_ontology (
    term TEXT PRIMARY KEY,
    term_name TEXT,
    onthology_type TEXT
);

CREATE TABLE channels (
    enst INT PRIMARY KEY,
    is_active_transport INT, -- bool
    conductance TEXT,
    permeability TEXT
);

CREATE TABLE carriers (
    enst INT PRIMARY KEY,
    class TEXT, -- symport, antiport, ...
    is_secondary INT, -- bool, uses secondary energy?
    to_lumen_pubchem_id TEXT, -- pubchem IDs of molecules carried to the lumen
    to_exterior_pubchem_id TEXT,
    rate_coefficient TEXT, -- trasport carry rate, like 1/2 Vmax
    rate_maximum TEXT -- Vmax
);


