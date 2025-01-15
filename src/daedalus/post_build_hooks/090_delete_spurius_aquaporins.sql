-- This removes some aquaporins that are included in the channels list
-- probably by the GO
DELETE FROM channels WHERE ensg IN (
	"ENSG00000086159",
	"ENSG00000103375",
	"ENSG00000103569",
	"ENSG00000135517",
	"ENSG00000143595",
	"ENSG00000161798",
	"ENSG00000165269",
	"ENSG00000165272",
	"ENSG00000167580",
	"ENSG00000171885",
	"ENSG00000178301",
	"ENSG00000240583"
);

-- This removes some SLCs that the GO introduces in the channels table
DELETE FROM channels WHERE ensg IN (
	SELECT ensg FROM solute_carriers
);

-- Same for pumps and ABCs
DELETE FROM channels WHERE ensg IN (
	SELECT ensg FROM pumps
);

DELETE FROM channels WHERE ensg IN (
	SELECT ensg FROM ABC_transporters
);
