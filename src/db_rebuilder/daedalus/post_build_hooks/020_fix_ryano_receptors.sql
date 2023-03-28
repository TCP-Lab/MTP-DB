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
  );
