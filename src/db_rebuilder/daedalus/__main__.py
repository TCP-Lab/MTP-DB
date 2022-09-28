from daedalus import OUT_ANCHOR
from daedalus.errors import Abort
from daedalus.make_db import generate_database
from daedalus.retrievers import retrieve_biomart

try:
    #generate_database(OUT_ANCHOR)
    retrieve_biomart()
except Abort:
    print("Abort!")