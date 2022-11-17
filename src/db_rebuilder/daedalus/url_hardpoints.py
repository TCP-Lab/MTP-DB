BIOMART = "http://www.ensembl.org/biomart/martservice"
BIOMART_XML_REQUESTS = {
    "IDs+desc": {
        "query": """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE Query>
<Query  virtualSchemaName = "default" formatter = "CSV" header = "0" uniqueRows = "1" count = "" datasetConfigVersion = "0.6" >

	<Dataset name = "hsapiens_gene_ensembl" interface = "default" >
		<Filter name = "biotype" value = "protein_coding"/>
		<Attribute name = "ensembl_gene_id_version" />
		<Attribute name = "ensembl_transcript_id_version" />
		<Attribute name = "description" />
		<Attribute name = "external_gene_name" />
		<Attribute name = "ensembl_peptide_id_version" />
		<Attribute name = "entrezgene_id" />
		<Attribute name = "pdb" />
		<Attribute name = "refseq_mrna" />
	</Dataset>
</Query>""",
        "colnames": [
            "ensembl_gene_id_version",
            "ensembl_transcript_id_version",
            "description",
            "external_gene_name",
            "ensembl_peptide_id_version",
            "entrezgene_id",
            "pdb",
            "refseq_mrna",
        ],
    },
    "hugo_symbols": {
        "query": """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE Query>
<Query  virtualSchemaName = "default" formatter = "CSV" header = "0" uniqueRows = "1" count = "" datasetConfigVersion = "0.6" >

	<Dataset name = "hsapiens_gene_ensembl" interface = "default" >
		<Filter name = "biotype" value = "protein_coding"/>
		<Attribute name = "hgnc_id" />
		<Attribute name = "hgnc_symbol" />
		<Attribute name = "ensembl_gene_id_version" />
	</Dataset>
</Query>""",
        "colnames": ["hgnc_id", "hgnc_symbol", "ensembl_gene_id_version"],
    },
    "GO_transcripts": {
        "query": """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE Query>
<Query  virtualSchemaName = "default" formatter = "CSV" header = "0" uniqueRows = "1" count = "" datasetConfigVersion = "0.6" >

	<Dataset name = "hsapiens_gene_ensembl" interface = "default" >
		<Filter name = "biotype" value = "protein_coding"/>
		<Attribute name = "ensembl_transcript_id" />
		<Attribute name = "go_id" />
	</Dataset>
</Query>""",
        "colnames": ["ensembl_transcript_id", "go_id"],
    },
    "GO_definitions": {
        "query": """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE Query>
<Query  virtualSchemaName = "default" formatter = "CSV" header = "0" uniqueRows = "1" count = "" datasetConfigVersion = "0.6" >

	<Dataset name = "hsapiens_gene_ensembl" interface = "default" >
		<Attribute name = "go_id" />
		<Attribute name = "name_1006" />
		<Attribute name = "definition_1006" />
		<Attribute name = "namespace_1003" />
	</Dataset>
</Query>""",
        "colnames": [
            "go_id",
            "name_1006",
            "definition_1006",
            "go_linkage_type",
            "namespace_1003",
        ],
    },
    "IDs": {
        "query": """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE Query>
<Query  virtualSchemaName = "default" formatter = "CSV" header = "0" uniqueRows = "1" count = "" datasetConfigVersion = "0.6" >

	<Dataset name = "hsapiens_gene_ensembl" interface = "default" >
		<Filter name = "biotype" value = "protein_coding"/>
		<Attribute name = "ensembl_gene_id" />
		<Attribute name = "ensembl_transcript_id" />
		<Attribute name = "ensembl_peptide_id" />
		<Attribute name = "version" />
		<Attribute name = "transcript_version" />
		<Attribute name = "peptide_version" />
		<Attribute name = "refseq_mrna" />
		<Attribute name = "refseq_peptide" />
	</Dataset>
</Query>""",
        "colnames": [
            "ensembl_gene_id",
            "ensembl_transcript_id",
            "ensembl_peptide_id",
            "version",
            "transcript_version",
            "peptide_version",
            "refseq_mrna",
            "refseq_peptide",
        ],
    },
}


TCDB = {
    "GO_to_TC": {
        "url": "https://www.tcdb.org/cgi-bin/projectv/public/go.py",
        "colnames": ["go_id", "tc_id", "family_name"],
    },
    "RefSeq_to_TC": {
        "url": "https://www.tcdb.org/cgi-bin/projectv/public/refseq.py",
        "colnames": ["refseq_id", "tc_id", "family_name"],
    },
    "TC_definitions": {
        "url": "https://www.tcdb.org/cgi-bin/projectv/public/families.py",
        "colnames": ["tc_id", "definition"],
    },
}

COSMIC = {
    "census": "https://cancer.sanger.ac.uk/cosmic/file_download/GRCh38/cosmic/v96/cancer_gene_census.csv",
    "IDs": "https://cancer.sanger.ac.uk/cosmic/file_download/GRCh38/cosmic/v96/CosmicHGNC.tsv.gz",
}

IUPHAR_DB = "https://www.guidetopharmacology.org/DATA/public_iuphardb_v2022.2.zip"
IUPHAR_COMPILED = {
    "targets+families": "https://www.guidetopharmacology.org/DATA/targets_and_families.csv",
    "ligands": "https://www.guidetopharmacology.org/DATA/ligands.csv",
    "interactions": "https://www.guidetopharmacology.org/DATA/interactions.csv",
}
