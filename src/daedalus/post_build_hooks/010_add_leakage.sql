-- This file adds the leakage ID to leakage channels

UPDATE channels SET gating_mechanism = "leakage" WHERE ensg IN (
    -- Potassium
    ------ KCNK (two pore)
    -- KCNK1
    "ENSG00000135750",
    -- KCNK2
    "ENSG00000082482",
    -- KCNK3
    "ENSG00000171303",
    -- KCNK5
    "ENSG00000164626",
    -- KCNK6
    "ENSG00000099337",
    -- KCNK7 -- NOT A FUNCTIONAL CHANNEL
    --"ENSG00000173338",
    -- KCNK9
    "ENSG00000169427",
    -- KCNK10
    "ENSG00000100433",
    -- KCNK12 -- NOT A FUNCTIONAL CHANNEL
    --"ENSG00000184261",
    -- KCNK13
    "ENSG00000152315",
    -- KCNK15 -- NOT A FUNCTIONAL CHANNEL
    --"ENSG00000124249",
    -- KCNK16
    "ENSG00000095981",
    -- KCNK17
    "ENSG00000124780",
    -- KCNK18
    "ENSG00000186795",
    -- KCNK4 -- IT IS NOT LEAKAGE, it it mechano
    -- "ENSG00000182450",
    -- Sodium
    ------ NALCN >> ENSG00000102452
    "ENSG00000102452"
    -- Chloride
    ------ ???
);

UPDATE channels SET gating_mechanism = "mechanosensitive" WHERE ensg IN (
    -- KCNK4
    "ENSG00000182450"
)
