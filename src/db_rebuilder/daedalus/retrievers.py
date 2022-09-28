import requests
from io import BytesIO

import pandas as pd

from logging import getLogger

from daedalus.url_hardpoints import BIOMART_XML_REQUESTS, BIOMART, TCDB
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


def retrieve_tcdb() -> dict[pd.DataFrame]:
    log.info("Retrieving data for TCDB.")
    
    result = {}
    for key, value in TCDB.items():
        log.info(f"Getting TCDB data {key}...")
        data = pbar_get(url = value)

        log.info("Casting...")
        df = pd.read_csv(data, sep="\t")

        result[key] = df
    
    return result

