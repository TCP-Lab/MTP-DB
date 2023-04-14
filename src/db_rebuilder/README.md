# Daedalus

This is the module that downloads and parses data from a variety of servers to get the raw database.

It was mainly written for speed in mind, so many edges are very rough right now.

## Making the database
To make the database, follow these steps:
```bash
git clone git@github.com:CMA-Lab/MTP-DB.git
cd MTP-DB/src/db_rebuilder

# I highly reccoment making a venv
python -m venv env
source env/bin/activate

pip install -r requirements.txt

# This will print out usage information
python -m daedalus -h
```
More documentation is coming soon (tm), as soon as the code stabilizes.

## Running tests
There are currently a handful of test, but broken. Will update soon(tm).
