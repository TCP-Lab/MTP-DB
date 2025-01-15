-- Some Ion channels are missing from both the IUPHAR database and the
-- HGNC. This adds them back in, with as much info as possible.
INSERT INTO channels (
    ensg, carried_solute, gating_mechanism
)
VALUES
    -- CLNS1A
    ('ENSG00000074201','Cl-','ligand'),
    -- DPP10
    ('ENSG00000175497','K+','voltage'),
    -- DPP6
    ('ENSG00000130226','K+','voltage'),
    -- KCNRG
    ('ENSG00000198553','K+',NULL),
    -- MCUB
    ('ENSG00000005059','Ca2+',NULL),
    -- MCUR1
    ('ENSG00000050393','Ca2+',NULL),
    -- MICU1
    ('ENSG00000107745','Ca2+',NULL),
    -- MICU2
    ('ENSG00000165487','Ca2+',NULL),
    -- MICU3
    ('ENSG00000155970','Ca2+',NULL),
    -- SMDT1
    ('ENSG00000183172','Ca2+',NULL),
    -- STIM1
    ('ENSG00000167323','Ca2+',NULL);

-- This insert might duplicate some rows, so I add here a de-duplication hook.
-- It's based on this answer: https://stackoverflow.com/questions/8190541/deleting-duplicate-rows-from-sqlite-database
DELETE FROM channels
WHERE rowid NOT IN (
  SELECT MIN(rowid)
  FROM channels
  GROUP BY ensg, gating_mechanism, carried_solute, relative_conductance, absolute_conductance
);
