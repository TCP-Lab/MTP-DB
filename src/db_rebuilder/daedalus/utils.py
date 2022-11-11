import base64
import functools
import json
import math
import re
import shutil
from dataclasses import dataclass
from io import BytesIO
from logging import getLogger
from numbers import Number
from typing import Optional

import pandas as pd
import requests
from daedalus.errors import Abort
from tqdm.auto import tqdm

log = getLogger(__name__)


def run(callable):
    return callable()


# For testing purposes
def get_mock_data():
    return "banana"


def pbar_get(url, params={}, disable=False) -> BytesIO:
    resp = requests.get(url=url, params=params, stream=True)

    # Show only if we can show INFOs
    disable = disable or log.getEffectiveLevel() > 20

    if resp.status_code > 299 or resp.status_code < 200:
        log.error(
            f"Request got response {resp.status_code} -- {resp.reason}. Aborting."
        )
        raise Abort

    log.info(f"Retrieving response from {url}...")
    size = int(resp.headers.get("Content-Length", 0))

    desc = "[Unknown file size]" if size == 0 else ""
    bytes = BytesIO()
    with tqdm.wrapattr(
        resp.raw, "read", total=size, desc=desc, disable=disable, delay=10
    ) as read_raw:
        shutil.copyfileobj(read_raw, bytes)

    bytes.seek(0)
    return bytes


def request_cosmic_download_url(url, auth_hash) -> str:
    payload = requests.get(url, headers={"Authorization": f"Basic {auth_hash}"})

    if payload.status_code > 299 or payload.status_code < 200:
        log.error(
            f"Could not log into COSMIC. Resp {payload.status_code} -- {payload.reason}"
        )
        raise Abort

    log.info("Decoding response...")
    blob = payload.content.decode("UTF-8")
    response = json.loads(blob)
    secure_url: str = response["url"]

    log.info("Success! Retrieved secure COSMIC download URL.")
    return secure_url


def make_cosmic_hash(username: str, password: str) -> str:
    # Cosmic are idiots, so they actually expect a newline in the encoded str
    # What the actual fuck.
    hash = base64.b64encode(f"{username}:{password}\n".encode("UTF-8")).decode("UTF-8")
    log.info(f"Computed hash: {hash}")
    return hash


pqdm = functools.partial(tqdm, disable=log.getEffectiveLevel() > 20)


@dataclass
class EnsemblID:
    full_id: str
    full_id_no_version: str
    type: str
    type_letter_prefix: str
    identifier: int
    version_number: Optional[int]


ENS_ID_MATCHER = re.compile("ENS(FM|GT|[EGPRT])([0-9]{11})(?:.([0-9]+))?")


def split_ensembl_ids(ensembl_id: str):
    """Splits an ensembl ID string into its components

    Args:
        ensembl_id (str): The ensembl id to split
    """
    assert ensembl_id.startswith("ENS"), "The passed string is not a valid ensembl ID."
    assert len(ensembl_id) >= 11, "The passed ensembl ID is too short."

    types = {
        "E": "exon",
        "FM": "protein family",
        "G": "gene",
        "GT": "gene tree",
        "P": "protein",
        "R": "regulatory feature",
        "T": "transcript",
    }

    match = ENS_ID_MATCHER.match(ensembl_id)

    if not match:
        log.error(f"Cannot match ID {ensembl_id}.")
        raise Abort

    try:
        type = types[match.groups()[0]]
    except KeyError:
        log.error(
            f"Error: cannot parse ENSEMBL ID. Type {match.groups()[0]} not valid."
        )
        raise Abort

    ver = match.groups()[2]
    if ver:
        ver = int(ver)

    parsed = EnsemblID(
        full_id=ensembl_id,
        full_id_no_version=f"ENS{match.groups()[0]}{match.groups()[1]}",
        type=type,
        type_letter_prefix=match.groups()[0],
        identifier=int(match.groups()[1]),
        version_number=ver,
    )

    return parsed


def represent_sql_type(data: pd.Series) -> list:
    result = []

    def tolerant_is_nan(item):
        try:
            check = math.isnan(item)
        except TypeError:
            check = False

        return check

    for item in data:
        if pd.isnull(item) or tolerant_is_nan(item):
            result.append("NULL")
        elif isinstance(item, Number):
            result.append(str(item))
        elif isinstance(item, str):
            result.append("'" + item.replace("'", "''") + "'")

    return result


def to_transaction(data: pd.DataFrame, table: str) -> str:
    log.info(
        f"Converting a {data.shape[0]} rows by {data.shape[1]} cols dataframe to a transaction string..."
    )

    sql = ["INSERT INTO " + table + " (" + ", ".join(data.columns) + ") VALUES "]
    for _, row in tqdm(data.iterrows(), total=data.shape[0]):
        sql.append("(" + ", ".join(represent_sql_type(row.values)) + "),")
    sql = "\n".join(sql)
    sql = sql.strip()[:-1]  # remove the trailing \n and the last comma
    sql = sql + ";"
    return sql


def sanity_check(check, message):
    log.info(f"Sanity check: {message}")
    try:
        assert check
    except AssertionError:
        log.critical(f"SANITY CHECK FAILED: {message}")
        raise Abort

    log.debug("Sanity check passed.")


def lmap(*args, **kwargs) -> list:
    """A not-lazy map."""
    return list(map(*args, **kwargs))


def execute_transaction(connection, transaction):
    log.info("Executing transaction...")
    connection.execute(transaction)


def print_duplicates(data: pd.DataFrame) -> None:
    print(data[~data.duplicated(keep=False)])


GENE_DESC_MATCHER = re.compile("^(.*?)\\[Source:(.*?);Acc:(.*?)\\]$")


@dataclass
class GeneDescription:
    original: str
    desc: str
    source: str
    accession: str


def split_gene_description(desc) -> GeneDescription:
    match = GENE_DESC_MATCHER.match(desc)

    if not match:
        log.error(f"Cannot parse description: {desc}")
        raise Abort

    return GeneDescription(
        original=desc,
        desc=match.groups()[0],
        source=match.groups()[1],
        accession=match.groups()[2],
    )


def recast(data: pd.DataFrame, mold: dict) -> pd.DataFrame:
    relevant: pd.DataFrame = data[list(mold.keys())]
    return relevant.rename(columns=mold)


def expand_column(data: pd.DataFrame, col: str, sep: str) -> pd.DataFrame:
    def split_strings(x):
        if isinstance(x, str):
            return x.split(sep)
        else:
            return x

    data[col] = lmap(lambda x: split_strings(x), data[col])

    return data.explode(col).drop_duplicates()
