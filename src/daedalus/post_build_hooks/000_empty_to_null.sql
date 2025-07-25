-- Some rows (very, very rarely), have "" instead of NULL.
-- This hook changes them or drops them

DELETE FROM solute_carriers WHERE
    ensg = "ENSG00000074621" AND carried_solute = "";

