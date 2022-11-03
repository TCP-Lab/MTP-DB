import base64
import functools
import json
import shutil
from io import BytesIO
from logging import getLogger

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
