import gzip
import multiprocessing
import re
import zipfile
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from logging import getLogger

import pandas as pd
from daedalus.errors import CacheKeyError
from daedalus.url_hardpoints import (
    BIOMART,
    BIOMART_XML_REQUESTS,
    COSMIC,
    IUPHAR_DB,
    TCDB,
)
from daedalus.utils import pbar_get, pqdm, request_cosmic_download_url, run
from typing_extensions import Self

log = getLogger(__name__)

CPUS = multiprocessing.cpu_count()


def retrieve_biomart() -> dict[pd.DataFrame]:
    log.info("Starting to retrieve from BioMart.")

    result = {}
    for key, value in BIOMART_XML_REQUESTS.items():
        log.info(f"Attempting to retrieve {key}...")
        data = pbar_get(url=BIOMART, params={"query": value["query"]})
        log.info("Casting response...")
        df = pd.read_csv(data, names=value["colnames"])

        result[key] = df

    log.info("Got all necessary data from BioMart.")

    return result


def retrieve_tcdb() -> dict[pd.DataFrame]:
    log.info("Retrieving data from TCDB.")

    result = {}
    for key, value in TCDB.items():
        log.info(f"Getting TCDB data {key}...")
        data = pbar_get(url=value["url"])

        log.info("Casting...")
        df = pd.read_csv(data, sep="\t", names=value["colnames"])

        result[key] = df

    log.info("Got all data from TCDB.")

    return result


def retrieve_cosmic_genes(auth_hash) -> dict[pd.DataFrame]:
    log.info("Retrieving COSMIC data...")

    result = {}
    for key, value in COSMIC.items():
        log.info(f"Retrieving data for {key}")
        secure_url = request_cosmic_download_url(value, auth_hash)
        data = pbar_get(secure_url)

        log.info("Casting response...")
        if key == "IDs":
            # The IDS are given as a compressed TSV file
            data = pd.read_csv(gzip.GzipFile(fileobj=data), sep="\t")
        else:
            try:
                data = pd.read_csv(data)
            except UnicodeDecodeError:
                log.info("Failed to parse data. Trying to uncompress...")
                data = pd.read_csv(gzip.GzipFile(fileobj=data))

        result[key] = data

    log.info("Done retrieving COSMIC data.")

    return result


class IUPHARGobbler:
    copy_line_re = re.compile("COPY (.*?) \\((.*?)\\) FROM stdin;")

    def __init__(self) -> None:
        self.tables = {}
        self.opened_table = False
        self.current_table_name = None
        self.current_table_cols = []
        self.current_table_data = []
        self.current_table_len = None

    def reset(self):
        self.current_table_name = None
        self.current_table_cols = []
        self.current_table_data = []
        self.current_table_len = None

    def gobble(self, line: str):
        line = line.rstrip("\n")

        if line.startswith("COPY") and self.opened_table is False:
            self.opened_table = True

            match = self.copy_line_re.match(line)
            self.current_table_name = match.groups()[0]
            self.current_table_cols = match.groups()[1].split(", ")
            self.current_table_len = len(self.current_table_cols)

            return

        if self.opened_table and line.startswith("\\."):
            self.opened_table = False

            df = pd.DataFrame(self.current_table_data, columns=self.current_table_cols)
            self.tables[self.current_table_name] = df

            self.reset()

            return

        if self.opened_table:
            if not len(line.split("\t")) == self.current_table_len:
                raise RuntimeError(
                    f"Line {line} does not fit in the current schema for table {self.current_table_name}: {self.current_table_cols}"
                )

            raw_data = line.split("\t")
            data = [x if x != "\\N" else None for x in raw_data]
            self.current_table_data.append(data)

            return


def retrieve_iuphar() -> dict[pd.DataFrame]:
    log.info("Getting IUPHAR database...")
    bytes = pbar_get(IUPHAR_DB)

    zip = zipfile.ZipFile(bytes)

    log.info("Running preliminary parsing operations...")
    gobbler = IUPHARGobbler()
    for line in pqdm(zip.open(zip.namelist()[0]).readlines()):
        line = line.decode("utf-8")
        gobbler.gobble(line)

    log.info("Done retrieving IUPHAR data")

    return gobbler.tables


class ResourceCache:
    __data = {}
    __populated = False

    def __init__(self, hooks) -> None:
        self.target_key = None
        self.__hooks = hooks

    def __call__(self, key: str) -> Self:
        self.target_key = key
        return self

    def populate(self):
        log.info("Populating resource cache...")
        with ProcessPoolExecutor(CPUS) as pool:
            # Just to be sure the orders are ok
            keys = deepcopy(list(self.__hooks.keys()))
            workers = [self.__hooks[key] for key in keys]

            items = pool.map(run, workers)

        for key, value in zip(self.__hooks.keys(), items):
            self.__data[key] = value

        self.__populated = True

    def __enter__(self):
        if self.target_key not in self.__hooks.keys():
            raise CacheKeyError(f"Invalid key: {self.target_key}")

        if self.__populated is False:
            self.populate()

        return deepcopy(self.__data[self.target_key])

    def __exit__(self, exc_type, exc, tb):
        pass
