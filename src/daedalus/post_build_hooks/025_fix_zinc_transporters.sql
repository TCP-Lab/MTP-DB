INSERT INTO solute_carriers (ensg, carried_solute) VALUES 
	("ENSG00000170385", "Zn2+"),
	("ENSG00000158014", "Zn2+"),
	("ENSG00000115194", "Zn2+"),
	("ENSG00000104154", "Zn2+"),
	("ENSG00000145740", "Zn2+"),
	("ENSG00000152683", "Zn2+"),
	("ENSG00000162695", "Zn2+"),
	("ENSG00000164756", "Zn2+"),
	("ENSG00000014824", "Zn2+"),
	("ENSG00000196660", "Zn2+"),
	("ENSG00000196660", "Mg2+");

DELETE FROM solute_carriers WHERE
	ensg IN (
		"ENSG00000170385",
		"ENSG00000158014",
		"ENSG00000115194",
		"ENSG00000104154",
		"ENSG00000145740",
		"ENSG00000152683",
		"ENSG00000162695",
		"ENSG00000164756",
		"ENSG00000014824",
		"ENSG00000196660",
		"ENSG00000196660"
	) AND
	carried_solute IS NULL;

-- Deduplication hook just in case.
-- It's based on this answer: https://stackoverflow.com/questions/8190541/deleting-duplicate-rows-from-sqlite-database
DELETE FROM solute_carriers
WHERE rowid NOT IN (
  SELECT MIN(rowid)
  FROM solute_carriers
  GROUP BY ensg, carried_solute, rate, net_charge, stoichiometry, port_type, is_secondary, direction, mode
);
