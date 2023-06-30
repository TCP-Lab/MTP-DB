"""Constants that are used throughout the program"""

# Re-export constants, so they can all be accessed from here
from daedalus import __version__
from daedalus.constants.url_hardpoints import (
    BIOMART,
    BIOMART_XML_REQUESTS,
    COSMIC,
    GO,
    HUGO,
    IUPHAR_COMPILED,
    IUPHAR_DB,
    PROTEIN_ATLAS,
    SLC_TABLES,
    TCDB,
)

__all__ = [
    "BIOMART",
    "BIOMART_XML_REQUESTS",
    "TCDB",
    "COSMIC",
    "IUPHAR_DB",
    "IUPHAR_COMPILED",
    "HUGO",
    "SLC_TABLES",
    "DESCRIPTION",
    "NAME",
    "EPILOG",
    "DB_NAME",
    "CACHE_NAME",
    "THESAURUS_FILE",
    "GO",
    "PROTEIN_ATLAS",
]

## TODO: It could be beneficial to bundle all of these constants into
# just one box and re-export just that.

DESCRIPTION = """
    >>> DAEDALUS <<<

This program builds the MTP-Db from information retrieved from online databases.
The rationale is that if the databases update, we also update accordingly.
We also add a pinch of manual curation to fill in the gaps of knowledge from the
online databases.

Some of the parsing steps from the remote databases to the local DB are
heuristic in nature, and therefore might give imperfect information.
Feel free to open issues on GitHub @ https://github.com/CMA-Lab/MTP-DB/issues
if you find any incorrect or missing information.
"""
"""A short description of Daedalus"""

NAME = "Daedalus, the MTP-Db rebuilder"
"""The name of the program, to be shown by Argparser"""

EPILOG = (
    "For more usage information, please refer to https://github.com/CMA-Lab/MTP-DB/"
)
"""Message shown by argparser at the bottom of the usage info"""

DB_NAME = f"MTPDB_v{__version__}.sqlite"
"""Name of the DB file to save as output"""

CACHE_NAME = f"MTPDB_datacache.pickle"
"""Name of the cache file to use to stash the downloaded data"""

THESAURUS_FILE = "thesaurus.csv"
"""Name of the local thesaurus file"""
