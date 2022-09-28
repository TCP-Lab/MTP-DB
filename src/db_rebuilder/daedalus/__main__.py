import base64
from daedalus import OUT_ANCHOR
from daedalus.errors import Abort
from daedalus.make_db import generate_database

import argparse

from daedalus.utils import make_cosmic_hash

parser = argparse.ArgumentParser()

parser.add_argument("cosmic_email")
parser.add_argument("cosmic_password")

args = parser.parse_args()

# This is pretty retarded but hey, who am I to judge the COSMIC project?
cosmic_hash = make_cosmic_hash(args.cosmic_email, args.cosmic_password)

try:
    generate_database(OUT_ANCHOR, cosmic_hash)
except Abort:
    print("Abort!")