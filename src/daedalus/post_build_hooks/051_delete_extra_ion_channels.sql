
-- These are SLC5A8 and SLC9C1 that are wrongly included in the channels list.
DELETE FROM channels WHERE ensg IN (
    "ENSG00000256870",
    "ENSG00000262217",
    "ENSG00000285044",
    "ENSG00000172139"
);
