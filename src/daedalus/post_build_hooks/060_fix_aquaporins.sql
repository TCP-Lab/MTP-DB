-- We need to move the VDAC1, VDAC2 and VDAC3 proteins from aquaporins to
-- ion channels.
DELETE FROM aquaporins WHERE ensg IN (
    "ENSG00000213585", "ENSG00000165637", "ENSG00000078668"
);

INSERT INTO channels (ensg, gating_mechanism, carried_solute) VALUES
    ("ENSG00000213585", "voltage", "anion"),
    ("ENSG00000165637", "voltage", "anion"),
    ("ENSG00000078668", "voltage", "anion");

-- This insert might duplicate some rows, so I add here a de-duplication hook.
-- It's based on this answer: https://stackoverflow.com/questions/8190541/deleting-duplicate-rows-from-sqlite-database
DELETE FROM channels
WHERE rowid NOT IN (
  SELECT MIN(rowid)
  FROM channels
  GROUP BY ensg, gating_mechanism, carried_solute, relative_conductance, absolute_conductance
);
