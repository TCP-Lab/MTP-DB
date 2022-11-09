import base64
import functools
import json
import re
import shutil
from dataclasses import dataclass
from io import BytesIO
from logging import getLogger
from typing import Optional

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
        resp.raw, "read", total=size, desc=desc, disable=disable
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
        type=type,
        type_letter_prefix=match.groups()[0],
        identifier=int(match.groups()[1]),
        version_number=ver,
    )

    return parsed
