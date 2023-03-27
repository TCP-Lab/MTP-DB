-- This file adds the leakage ID to leakage channels

UPDATE channels SET gating_mechanism = "" WHERE ensg IN (
    -- Potassium
    ------ KCNK (two pore)
    "ENSG00000135750",
    "ENSG00000100433",
    "ENSG00000184261",
    "ENSG00000152315",
    "ENSG00000124249",
    "ENSG00000095981",
    "ENSG00000124780",
    "ENSG00000186795",
    "ENSG00000082482",
    "ENSG00000182450",
    "ENSG00000099337",
    -- Sodium
    ------ NALCN >> ENSG00000102452
    "ENSG00000102452"
    -- Chloride
    ------ ???
);
