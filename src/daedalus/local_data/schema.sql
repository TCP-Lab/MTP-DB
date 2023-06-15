CREATE TABLE gene_ids (
    ensg_version TEXT UNIQUE NOT NULL, -- from biomart > IDs+desc > gene_stable_id_version
    ensg TEXT PRIMARY KEY, -- from biomart > IDs+desc > gene_stable_id_version
    ensg_version_leaf INT NOT NULL -- from biomart > IDs+desc > gene_stable_id_version
);

CREATE TABLE transcript_ids (
    ensg TEXT NOT NULL, -- from biomart > IDs+desc > gene_stable_id_version
    enst TEXT PRIMARY KEY, -- from biomart > IDs+desc > transcript_stable_id_version
    enst_version TEXT UNIQUE NOT NULL, -- same as enst
    enst_version_leaf INT NOT NULL, -- same as enst
    is_canonical_isoform INT NOT NULL -- bool
);

CREATE TABLE mrna_refseq (
    -- These cannot be unique, as some refseq IDs are missing
    enst TEXT NOT NULL, -- from biomart > IDs+desc > transcript_stable_id_version
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
    ensg TEXT, -- from biomart > IDs+desc > gene_stable_id_version
    hugo_gene_id TEXT, -- from biomart > hugo_symbols > hgnc_id
    hugo_gene_symbol TEXT, -- from biomart > hugo_symbols > hugo_gene symbol
    -- (double check with the description field below)
    hugo_gene_name TEXT -- from biomart > IDs+desc > description
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

-- It is purpusefully generic, but we can talk about it...
CREATE TABLE cosmic_genes (
    ensg TEXT NOT NULL, -- If the ensg is here, it is in the cosmic database
    is_hallmark INT NOT NULL, -- If true, the gene is a hallmark gene is some tumor type
    tumor_type NOT NULL, -- The tumor type related to this gene
    is_somatic NOT NULL, -- If true, the gene was detected as somatically mutated
    is_germline NOT NULL -- If true, the gene was detected as germline mutated
);


----- NOVEL DATA ------
CREATE TABLE channels (
    ensg TEXT,
    -- gating
    gating_mechanism TEXT,
    --
    carried_solute TEXT,
    relative_conductance REAL,
    absolute_conductance REAL
);

CREATE TABLE aquaporins (
    ensg TEXT,
    expression_tissue TEXT -- manual insertion
);

CREATE TABLE solute_carriers (
    ensg TEXT, -- I don't make this a primary key as there will probably be duplicated rows:
    -- Probably, each ensg - carried solute combo will be unique.
    carried_solute TEXT,
    rate REAL,
    net_charge INT,
    stoichiometry INT, -- o simili
    port_type TEXT, -- uni- anti- symp-porter
    is_secondary INT, -- (active secondary)
    direction TEXT,
    mode INT -- TODO: Why do we need this?
);

CREATE TABLE pumps (
    ensg TEXT, -- See the note on uniqueness for solute carriers
    net_charge INT,
    carried_solute TEXT,
    rate REAL,
    direction TEXT,
    stoichiometry INT,
    mode INT
);

CREATE TABLE ABC_transporters (
    ensg TEXT, -- See the note on uniqueness for solute carriers
    carried_solute TEXT,
    net_charge INT,
    stoichiometry INT,
    rate REAL,
    direction TEXT,
    mode INT
);
