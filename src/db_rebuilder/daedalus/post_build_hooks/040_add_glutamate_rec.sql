--- Rationale: The glutamate receptors (in the brain) are present in the
-- "channels" table but since the HGNC does not have them correctly classified
-- as permeable to something and the IUPHAR has no conductivity info on them,
-- they are currently without permeability information.

-- First pass: They are ALL permeable to sodium + they are all ligand gated
UPDATE channels SET
    gating_mechanism = "ligand",
    carried_solute = "Na+"
WHERE ensg IN (
    -- AMPA
    "ENSG00000155511",
    "ENSG00000120251",
    "ENSG00000125675",
    "ENSG00000152578",
    -- DELTA
    -- NOTE: I have little info on GRID2, so i'm keeping it blank for now
    --"ENSG00000182771",
    --"ENSG00000152208",
    -- KAINATE
    "ENSG00000171189",
    "ENSG00000164418",
    "ENSG00000163873",
    "ENSG00000149403",
    "ENSG00000105737",
    -- NMDA
    "ENSG00000176884",
    "ENSG00000183454",
    "ENSG00000273079",
    "ENSG00000161509",
    "ENSG00000105464",
    "ENSG00000198785",
    "ENSG00000116032"
);

-- Second pass: specific permeabilities of subunits
-- AMPAs, Kainate and NMDAs are also permeable to potassium
INSERT INTO channels (
    ensg, gating_mechanism, carried_solute
) VALUES
    -- KAINATE
    ("ENSG00000171189", "ligand", "K+"),
    ("ENSG00000164418", "ligand", "K+"),
    ("ENSG00000163873", "ligand", "K+"),
    ("ENSG00000149403", "ligand", "K+"),
    ("ENSG00000105737", "ligand", "K+"),
    -- NMDA
    ("ENSG00000176884", "ligand", "K+"),
    ("ENSG00000183454", "ligand", "K+"),
    ("ENSG00000273079", "ligand", "K+"),
    ("ENSG00000161509", "ligand", "K+"),
    ("ENSG00000105464", "ligand", "K+"),
    ("ENSG00000198785", "ligand", "K+"),
    ("ENSG00000116032", "ligand", "K+"),
    -- AMPA
    ("ENSG00000155511", "ligand", "K+"),
    ("ENSG00000120251", "ligand", "K+"),
    ("ENSG00000125675", "ligand", "K+"),
    ("ENSG00000152578", "ligand", "K+");

-- NMDAs are also permeable to calcium
INSERT INTO channels (
    ensg, gating_mechanism, carried_solute
) VALUES
    -- NMDA
    ("ENSG00000176884", "ligand", "Ca2+"),
    ("ENSG00000183454", "ligand", "Ca2+"),
    ("ENSG00000273079", "ligand", "Ca2+"),
    ("ENSG00000161509", "ligand", "Ca2+"),
    ("ENSG00000105464", "ligand", "Ca2+"),
    ("ENSG00000198785", "ligand", "Ca2+"),
    ("ENSG00000116032", "ligand", "Ca2+");
