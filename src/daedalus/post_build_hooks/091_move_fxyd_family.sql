-- Rationale: the FXYD-family of proteins regulate the action of the NA/K
-- transporter, not a channel. The GO annotates them wrong. Here, we set them
-- to be transporters, not channels.

-- First, get rid of the FXYD genes in the channels table
DELETE FROM channels
    WHERE ensg IN (
        "ENSG00000266964", -- FXYD1
        "ENSG00000137731", -- FXYD2
        "ENSG00000089356", -- FXYD3
        "ENSG00000150201", -- FXYD4
        "ENSG00000089327", -- FXYD5
        "ENSG00000137726", -- FXYD6
        "ENSG00000221946" -- FXYD7
    );

-- Second, add them back in, in the pumps table
INSERT INTO pumps (ensg, carried_solute) VALUES
    -- FXYD1
    ("ENSG00000266964", "K+"),
    ("ENSG00000266964", "Na+"),
    ("ENSG00000266964", "ion"),
    ("ENSG00000266964", "cation"),
    -- FXYD2
    ("ENSG00000137731", "K+"),
    ("ENSG00000137731", "Na+"),
    ("ENSG00000137731", "ion"),
    ("ENSG00000137731", "cation"),
    -- FXYD3
    ("ENSG00000089356", "K+"),
    ("ENSG00000089356", "Na+"),
    ("ENSG00000089356", "ion"),
    ("ENSG00000089356", "cation"),
    -- FXYD4
    ("ENSG00000150201", "K+"),
    ("ENSG00000150201", "Na+"),
    ("ENSG00000150201", "ion"),
    ("ENSG00000150201", "cation"),
    -- FXYD5
    ("ENSG00000089327", "K+"),
    ("ENSG00000089327", "Na+"),
    ("ENSG00000089327", "ion"),
    ("ENSG00000089327", "cation"),
    -- FXYD6
    ("ENSG00000137726", "K+"),
    ("ENSG00000137726", "Na+"),
    ("ENSG00000137726", "ion"),
    ("ENSG00000137726", "cation"),
    -- FXYD7
    ("ENSG00000221946", "K+"),
    ("ENSG00000221946", "Na+"),
    ("ENSG00000221946", "ion"),
    ("ENSG00000221946", "cation");
