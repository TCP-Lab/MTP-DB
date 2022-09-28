from copy import deepcopy
from concurrent.futures import ProcessPoolExecutor
from io import BytesIO
import json
import multiprocessing
import shutil
import base64

import requests
from tqdm.auto import tqdm

from daedalus.errors import Abort, CacheKeyError
from logging import getLogger

log = getLogger(__name__)

CPUS = multiprocessing.cpu_count()

def run(callable):
    return callable()

# For testing purposes
def get_mock_data():
    return "banana"

class ResourceCache:
    __hooks = {
        "__mock": get_mock_data
    }
    __data = {}
    __populated = False

    def __init__(self, key) -> None:
        self.target_key = key

    def populate(self):
        with ProcessPoolExecutor(CPUS) as pool:
            # Just to be sure the orders are ok
            keys = deepcopy(list(self.__hooks.keys()))
            workers = [self.__hooks[key] for key in keys]

            items = pool.map(run, workers)
        
        for key, value in zip(self.__hooks.keys(), items):
            self.__data[key] = value

    
    def __enter__(self):
        if self.target_key not in self.__hooks.keys():
            raise CacheKeyError(f"Invalid key: {self.__key}")
        
        if self.__populated is False:
            self.populate()

        return deepcopy(self.__data[self.target_key])

    
    def __exit__(self, exc_type, exc, tb):
        pass

def pbar_get(url, params = {}) -> requests.Response:
    resp = requests.get(url=url, params=params, stream=True)

    if resp.status_code != 200:
        log.error(f"Request got response {resp.status_code} -- {resp.reason}. Aborting.")
        raise Abort
    
    log.info(f"Retrieving response from {url}...")
    size = int(resp.headers.get("Content-Length", 0))

    desc = "[Unknown file size]" if size == 0 else ""
    bytes = BytesIO()
    with tqdm.wrapattr(resp.raw, "read", total=size, desc = desc) as read_raw:
        shutil.copyfileobj(read_raw, bytes)
    
    bytes.seek(0)
    return bytes

def request_cosmic_download_url(url, auth_hash) -> str:
    payload = requests.get(url, headers={"Authorization": f"Basic {auth_hash}"})

    if payload.status_code != 200:
        log.error(f"Could not log into COSMIC. Resp {payload.status_code} -- {payload.reason}")
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
    return base64.b64encode(f"{username}:{password}\n".encode()).decode()
