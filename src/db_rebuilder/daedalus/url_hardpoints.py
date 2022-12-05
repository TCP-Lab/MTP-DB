BIOMART = "http://www.ensembl.org/biomart/martservice"
"""The Url used by Biomart to accept requests"""
BIOMART_XML_REQUESTS = {
    "IDs+desc": {
        "query": """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE Query>
<Query  virtualSchemaName = "default" formatter = "CSV" header = "0" uniqueRows = "0" count = "" datasetConfigVersion = "0.6" >

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
<Query  virtualSchemaName = "default" formatter = "CSV" header = "0" uniqueRows = "0" count = "" datasetConfigVersion = "0.6" >

	<Dataset name = "hsapiens_gene_ensembl" interface = "default" >
		<Filter name = "biotype" value = "protein_coding"/>
		<Attribute name = "hgnc_id" />
		<Attribute name = "hgnc_symbol" />
		<Attribute name = "ensembl_gene_id_version" />
	</Dataset>
</Query>""",
        "colnames": ["hgnc_id", "hgnc_symbol", "ensembl_gene_id_version"],
    },
    "IDs": {
        "query": """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE Query>
<Query  virtualSchemaName = "default" formatter = "CSV" header = "0" uniqueRows = "0" count = "" datasetConfigVersion = "0.6" >

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
"""Hardpoints with Biomart data.

In the form of 'table_name': {'query': xlm_query, 'colnames': [list of colnames]}
"""

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
"""TCDB hardpoints

In the form of 'table_name': {'url': the download url, 'colnames': [list of colnames]}
"""

COSMIC = {
    "census": "https://cancer.sanger.ac.uk/cosmic/file_download/GRCh38/cosmic/v96/cancer_gene_census.csv",
    "IDs": "https://cancer.sanger.ac.uk/cosmic/file_download/GRCh38/cosmic/v96/CosmicHGNC.tsv.gz",
}
"""COSMIC download urls of precompiled data"""

IUPHAR_DB = "https://www.guidetopharmacology.org/DATA/public_iuphardb_v2022.2.zip"
"""URL to the download of the full IUPHAR database"""
IUPHAR_COMPILED = {
    "targets+families": "https://www.guidetopharmacology.org/DATA/targets_and_families.csv",
    "ligands": "https://www.guidetopharmacology.org/DATA/ligands.csv",
    "interactions": "https://www.guidetopharmacology.org/DATA/interactions.csv",
}
"""URLs to the compiled IUPHAR data from their downloads page"""

HUGO = {
    "nomenclature": "http://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/archive/monthly/tsv/hgnc_complete_set_2021-03-01.txt",
    "groups": {
        # I could download json files, but most of the data is flat anyway, so...
        "endpoint": "https://www.genenames.org/cgi-bin/genegroup/download?id={id}&type=branch",
        "IDs": {
            "ion_channels": 177,  # These names are the ones ending up in the DataDict
            "sodium_ion_channels": 179,
            "calcium_ion_channels": 182,
            "potassium_ion_channels": 183,
            "chloride_ion_channels": 278,
            "porins": 304,
            "aquaporins": 305,
            "ligand_gated_ion_channels": 161,
            "voltage_gated_ion_channels": 178,
            "ABC_transporters": 417,
            "solute_carriers": 752,
        },
    },
}
"""Hugo downloads as found on their download pages"""

SLC_TABLES = "http://slc.bioparadigms.org/"
