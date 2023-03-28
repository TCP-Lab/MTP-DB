--- Rationale: The GABA-A receptors (in the brain) are present in the
-- "channels" table but since the HGNC does not have them correctly classified
-- as permeable to something and the IUPHAR has no conductivity info on them,
-- they are currently without permeability information.

UPDATE channels SET
    gating_mechanism = "ligand",
    carried_solute = "Cl-",
    relative_conductance = 1,
    absolute_conductance = NULL
WHERE ensg IN (
    "ENSG00000022355",
    "ENSG00000151834",
    "ENSG00000011677",
    "ENSG00000109158",
    "ENSG00000186297",
    "ENSG00000145863",
    "ENSG00000163288",
    "ENSG00000145864",
    "ENSG00000166206",
    "ENSG00000187730",
    "ENSG00000102287",
    "ENSG00000163285",
    "ENSG00000113327",
    "ENSG00000182256",
    "ENSG00000094755",
    "ENSG00000268089",
    "ENSG00000146276",
    "ENSG00000111886",
    "ENSG00000183185"
);

-- Reviewed in https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2648504/
-- the HCO3- conductance is ~0.2/0.4 of the Cl- conductance
INSERT INTO channels (
    ensg, gating_mechanism, carried_solute, relative_conductance, absolute_conductance
) VALUES
    ("ENSG00000022355", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000151834", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000011677", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000109158", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000186297", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000145863", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000163288", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000145864", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000166206", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000187730", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000102287", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000163285", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000113327", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000182256", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000094755", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000268089", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000146276", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000111886", "ligand", "HCO3-", 0.3, NULL),
    ("ENSG00000183185", "ligand", "HCO3-", 0.3, NULL);
