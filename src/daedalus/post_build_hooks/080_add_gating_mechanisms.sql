-- Rationale: The GO adds a series of channels and their permeabilities, but
-- we still miss their gating mechanims. This adds it back in after the change
-- in the 050_add_missing_ion_channels.sql post-build-hook change.

UPDATE channels SET gating_mechanism = "voltage" WHERE ensg IN(
	"ENSG00000169282",
	"ENSG00000069424",
	"ENSG00000170049",
	"ENSG00000180509",
	"ENSG00000159197",
	"ENSG00000175538",
	"ENSG00000152049",
	"ENSG00000176076",
	"ENSG00000182132",
	"ENSG00000120049",
	"ENSG00000115041",
	"ENSG00000185774",
	"ENSG00000145936",
	"ENSG00000197584",
	"ENSG00000171121",
	"ENSG00000135643",
	"ENSG00000136546"
);

