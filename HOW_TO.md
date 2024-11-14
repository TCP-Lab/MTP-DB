# How to

This page compiles common operations that you might want to do when using the MTP-DB.

## How to find all GAP junctions?
This SQL gets you all the GAP junction ENSGs. They are best detected by their gene name, as the TCDB families seem to be incomplete:
```sql
SELECT ensg
FROM gene_names
WHERE
	hugo_gene_symbol like "GJ%" OR
	hugo_gene_symbol like "PANX%"
```

