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
    enst TEXT, -- from biomart > IDs+desc > ensembl_transcript_id_version
    refseq_transcript_id TEXT UNIQUE NOT NULL -- from biomart > IDs+desc > refseq_mrna
    -- refseq_transcript_id_version INT NOT NULL -- MISSING?? No version for refseq?
    -- refseq_transcrpit_id_version_leaf INT NOT NULL -- See aboveref
);

-- There are more pdb_ids than ensts, as a single transcript can have multiple deposited structs
CREATE TABLE protein_structures (
    enst TEXT,
    pdb_id TEXT,
    refseq_protein_id TEXT
);

CREATE TABLE gene_names (
    enst TEXT, -- from biomart > IDs+desc > ensembl_gene_id_version
    hugo_gene_id TEXT PRIMARY KEY, -- from biomart > hugo_symbols > hgnc_id
    hugo_gene_symbol TEXT UNIQUE NOT NULL, -- from biomart > hugo_symbols > hugo_gene symbol
    -- (double check with the description field below)
    hugo_gene_name TEXT NOT NULL, -- from biomart > IDs+desc > description
    gene_symbol_synonyms TEXT -- ???
);

CREATE TABLE iuphar_ids (
    ensg INT PRIMARY KEY, -- from biomart > IDs+desc > ensembl_gene_id_version
    target_id TEXT UNIQUE NOT NULL, -- unsure if this is unique
    target_name TEXT NOT NULL, --
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

CREATE TABLE gene_ontology_description (
    term TEXT PRIMARY KEY,
    term_name TEXT,
    onthology_type TEXT
);

CREATE TABLE transcript_gene_ontology (
    term TEXT PRIMARY KEY,
    enst TEXT
);

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
