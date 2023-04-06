# MTP-DB - The Membrane Transport Protein Database

Welcome to the repository for the MTP-Db, a database that aims to collect information regarding the transportome, and the proteins that make it up.

The database is a `.sqlite` file.

The project is composed in many parts:
- `./src/db_rebuilder` contains a Python package, `daedalus`, that remakes the database by polling remote databases.
- `./src/geneset_maker` contains a Python script, `make_genesets.py` that makes a series of sets of genes based on the database.
- `./src/gsea_runner` contains R scripts that allow running the genesets from the previous module with GSEA on various types of data, such as the TCGA or arbitrary lists made by tools like `bioTEA`.
- `./src/mtpdb` is currently empty, but might eventually contain a GUI program that allows for easy retrieval of datasets from the DB.

Each submodule has its own README. Please refer to those for more information.

## Contributing
If you want to contribute, please use the `pre-commit` hooks that you can find in the top-level folder.

More detailed contributing guides coming soon.s
