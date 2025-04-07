-- Rationale: the RYR receptors are not only ligand gated, but also
-- voltage gated. This adds this info in, as the IUPHAR and the HGNC fail to
-- annotate them as such (only marking them as ligand gated).

INSERT INTO channels (
    ensg, gating_mechanism, carried_solute, relative_conductance, absolute_conductance
) SELECT
    ensg, "voltage", carried_solute, relative_conductance, absolute_conductance
  FROM channels
  WHERE ensg IN (
    "ENSG00000196218", -- ryr1
    "ENSG00000198626", -- ryr2
    "ENSG00000198838" -- ryr3
  ) AND (gating_mechanism != "voltage" OR gating_mechanism IS NULL);

-- There are some well known calcium channels that are not annotated as such
INSERT INTO channels (
    ensg, carried_solute
) SELECT
    ensg, "Ca2+"
  FROM channels
  WHERE ensg IN (
    "ENSG00000120903", -- CHRNA2
    "ENSG00000101204", -- CHRNA4
    "ENSG00000103335", -- PIEZO1
    "ENSG00000154864", -- PIEZO2
    "ENSG00000089041", -- P2RX7
    "ENSG00000165637", -- VDAC2
    "ENSG00000187848", -- P2RX2
    "ENSG00000080644", -- CHRNA3
    "ENSG00000169684", -- CHRNA5
    "ENSG00000166736", -- HTR3A
    "ENSG00000213585", -- VDAC1
    "ENSG00000109991", -- P2RX3
    "ENSG00000078668", -- VDAC3
    "ENSG00000170289", -- CNGB3
    "ENSG00000120903", -- CHRNA2
    "ENSG00000147434" -- CHRNA6
) AND (carried_solute != "Ca2+" OR carried_solute IS NULL);

-- TRP channels are NOT voltage gated
UPDATE channels SET
    gating_mechanism = NULL
WHERE ensg IN (
    "ENSG00000133107",
    "ENSG00000142185",
    "ENSG00000274965",
    "ENSG00000137672",
    "ENSG00000100991",
    "ENSG00000069018",
    "ENSG00000138741",
    "ENSG00000111199",
    "ENSG00000165125",
    "ENSG00000127412",
    "ENSG00000144481",
    "ENSG00000274348",
    "ENSG00000276971",
    "ENSG00000072315",
    "ENSG00000187688",
    "ENSG00000104321",
    "ENSG00000092439",
    "ENSG00000196689",
    "ENSG00000083067",
    "ENSG00000119121",
    "ENSG00000070985",
    "ENSG00000130529",
    "ENSG00000167723",
    "ENSG00000144935",
    "ENSG00000134160"
) AND (gating_mechanism == "voltage");

