-- We need to move the VDAC1, VDAC2 and VDAC3 proteins from aquaporins to
-- ion channels.
DELETE FROM aquaporins WHERE ensg IN (
    "ENSG00000213585", "ENSG00000165637", "ENSG00000078668"
);

INSERT INTO channels (ensg, gating_mechanism, carried_solute) VALUES
    ("ENSG00000213585", "voltage", "anion"),
    ("ENSG00000165637", "voltage", "anion"),
    ("ENSG00000078668", "voltage", "anion");
