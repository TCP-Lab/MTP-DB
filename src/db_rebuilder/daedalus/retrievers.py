import requests
from io import BytesIO

import pandas as pd

from logging import getLogger

from daedalus.errors import Abort
from daedalus.url_hardpoints import BIOMART_XML_REQUESTS, BIOMART
from daedalus.utils import pbar_get

log = getLogger(__name__)

def retrieve_biomart() -> dict[pd.DataFrame]:
    log.info("Starting to retrieve from BioMart.")

    result = {}
    for key, value in BIOMART_XML_REQUESTS.items():
        log.info(f"Attempting to retrieve {key}...")
        data = pbar_get(url = BIOMART, params={"query": value})
        log.info("Casting response...")
        df = pd.read_csv(data)

        result[key] = df
    
    log.info("Got all necessary data from BioMart.")

    return result

