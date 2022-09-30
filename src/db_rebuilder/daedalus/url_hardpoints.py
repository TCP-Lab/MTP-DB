
BIOMART = "http://www.ensembl.org/biomart/martservice"
BIOMART_XML_REQUESTS = {
    "IDs+desc" : '''<?xml version="1.0" encoding="UTF-8"?>
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
</Query>''',
    "hugo_symbols": '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE Query>
<Query  virtualSchemaName = "default" formatter = "CSV" header = "0" uniqueRows = "0" count = "" datasetConfigVersion = "0.6" >
			
	<Dataset name = "hsapiens_gene_ensembl" interface = "default" >
		<Filter name = "biotype" value = "protein_coding"/>
		<Attribute name = "hgnc_id" />
		<Attribute name = "hgnc_symbol" />
		<Attribute name = "ensembl_gene_id_version" />
	</Dataset>
</Query>''',
    "GO_transcrips": '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE Query>
<Query  virtualSchemaName = "default" formatter = "CSV" header = "0" uniqueRows = "0" count = "" datasetConfigVersion = "0.6" >
			
	<Dataset name = "hsapiens_gene_ensembl" interface = "default" >
		<Filter name = "biotype" value = "protein_coding"/>
		<Attribute name = "ensembl_transcript_id_version" />
		<Attribute name = "go_id" />
		<Attribute name = "definition_1006" />
		<Attribute name = "name_1006" />
		<Attribute name = "go_linkage_type" />
		<Attribute name = "namespace_1003" />
	</Dataset>
</Query>'''
}


TCDB = {
    "GO_to_TC": "https://www.tcdb.org/cgi-bin/projectv/public/go.py",
    "RefSeq_to_TC": "https://www.tcdb.org/cgi-bin/projectv/public/refseq.py",
    "TC_definitions": "https://www.tcdb.org/cgi-bin/projectv/public/families.py"
}

COSMIC = {
    "census": "https://cancer.sanger.ac.uk/cosmic/file_download/GRCh38/cosmic/v96/cancer_gene_census.csv",
    "IDs": "https://cancer.sanger.ac.uk/cosmic/file_download/GRCh38/cosmic/v96/CosmicHGNC.tsv.gz"
}

IUPHAR_DB = "https://www.guidetopharmacology.org/DATA/public_iuphardb_v2022.2.zip"
