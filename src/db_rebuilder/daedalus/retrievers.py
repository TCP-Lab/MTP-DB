import requests
from io import BytesIO

import pandas as pd

from logging import getLogger

from daedalus.url_hardpoints import BIOMART_XML_REQUESTS, BIOMART, COSMIC, TCDB
from daedalus.utils import pbar_get, request_cosmic_download_url

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
    log.info("Retrieving data from TCDB.")
    
    result = {}
    for key, value in TCDB.items():
        log.info(f"Getting TCDB data {key}...")
        data = pbar_get(url = value)

        log.info("Casting...")
        df = pd.read_csv(data, sep="\t")

        result[key] = df
    
    log.info("Got all data from TCDB.")
    
    return result

def retrieve_cosmic_genes(auth_hash) -> pd.DataFrame:
    log.info("Retrieving COSMIC data...")

    result = {}
    for key, value in COSMIC.items():
        log.info(f"Retrieving data for {key}")
        secure_url = request_cosmic_download_url(value, auth_hash)

        data = pbar_get(secure_url)

        result[key] = data
    
    log.info("Done retrieving COSMIC data.")

    return result
        
