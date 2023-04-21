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
    -- KCNAB1
    ('ENSG00000169282','K+','voltage'),
    -- KCNAB2
    ('ENSG00000069424','K+','voltage'),
    -- KCNAB3
    ('ENSG00000170049','K+','voltage'),
    -- KCNE1
    ('ENSG00000180509','K+','voltage'),
    -- KCNE2
    ('ENSG00000159197','K+','voltage'),
    -- KCNE3
    ('ENSG00000175538','K+','voltage'),
    -- KCNE4
    ('ENSG00000152049','K+','voltage'),
    -- KCNE5
    ('ENSG00000176076','K+','voltage'),
    -- KCNIP1
    ('ENSG00000182132','K+','voltage'),
    -- KCNIP2
    ('ENSG00000120049','K+','voltage'),
    -- KCNIP3
    ('ENSG00000115041','K+','voltage'),
    -- KCNIP4
    ('ENSG00000185774','K+','voltage'),
    -- KCNMB1
    ('ENSG00000145936','K+','voltage'),
    -- KCNMB2
    ('ENSG00000197584','K+','voltage'),
    -- KCNMB3
    ('ENSG00000171121','K+','voltage'),
    -- KCNMB4
    ('ENSG00000135643','K+','voltage'),
    -- KCNRG
    ('ENSG00000198553','K+',NULL),
    -- MCU
    ('ENSG00000156026','Ca2+',NULL),
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
    -- PKD1
    ('ENSG00000008710','Ca2+',NULL),
    -- PKD1L1
    ('ENSG00000158683','Ca2+',NULL),
    -- PKD1L2
    ('ENSG00000166473','Ca2+',NULL),
    -- PKD1L3
    ('ENSG00000277481','Ca2+',NULL),
    -- PKDREJ
    ('ENSG00000130943','Ca2+',NULL),
    -- SCN7A
    ('ENSG00000136546','Na2+','voltage'),
    -- SMDT1
    ('ENSG00000183172','Ca2+',NULL),
    -- STIM1
    ('ENSG00000167323','Ca2+',NULL),
    -- STIM2
    ('ENSG00000109689','Ca2+',NULL);
