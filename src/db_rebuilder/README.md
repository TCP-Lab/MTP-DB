This is the thing that downloads and parses data from a variety of servers to get the first "base" version of the database.

It was not written with elegance in mind, so the code is terrible.

## Running tests
To correctly run tests, we need a cosmic hash to log into the cosmic DB. Make a `secrets.json` file in `daedalus/tests/` and insert:

- A `cosmic_hash` key with your cosmic hash. An example on how to do this [is detailed here](https://cancer.sanger.ac.uk/cosmic/file_download_info?data=GRCh38%2Fcosmic%2Fv96%2FCosmicHGNC.tsv.gz).
- A `cosmic_username` key with your cosmic username;
- A `cosmic_password` key with your cosmic password (to test out the hashing functions);
