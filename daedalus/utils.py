import base64
import functools
import json
import math
import re
import shutil
from dataclasses import dataclass
from importlib import resources
from io import BytesIO, StringIO
from logging import getLogger
from numbers import Number
from typing import Any, Optional

import numpy as np
import pandas as pd
import requests
from tqdm.auto import tqdm

from daedalus import local_data, post_build_hooks
from daedalus.constants import THESAURUS_FILE
from daedalus.errors import Abort

log = getLogger(__name__)


# For testing purposes
def get_mock_data():
    return "banana"


def pbar_get(url: str, params: dict = {}, disable: bool = False) -> BytesIO:
    """A requests.get() call with an added download bar

    The bar is suppressed if the log has an effective level of more than 20
    - anything greater than INFO - so the program runs silently if we don't want
    logging.

    Raises Abort, killing Daedalus if the download fails. This is intended.

    Tries to estimate download sizes from the response headers.

    Args:
        url (str): The url to download from
        params (dict, optional): The params to pass to the GET request. Defaults to {}.
        disable (bool, optional): Disable the progress bar?. Defaults to False.

    Raises:
        Abort: If the request failed.

    Returns:
        BytesIO: The downloaded data, as bytes wrapped in a BytesIO object.
    """
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
    # I add some delay so the logging does not get (too) mangled up.
    # The download bars are there just to check on very long download tasks,
    # like from biomart.
    with tqdm.wrapattr(
        resp.raw, "read", total=size, desc=desc, disable=disable, delay=30
    ) as read_raw:
        shutil.copyfileobj(read_raw, bytes)

    # Reset the pointer after we've written all the data
    bytes.seek(0)
    return bytes


def request_cosmic_download_url(url: str, auth_hash: str) -> str:
    """Request a download url from COSMIC, "logging in" with a login hash.

    The downloaded url will be given with all attached parameters, so it has to
    be used as-is. >> I've tried to separate them, but then the download always
    fails.

    Args:
        url (str): The url to request.
        auth_hash (str): The auth hash to login with

    Raises:
        Abort: If the login was unsuccessful

    Returns:
        str: The valid download url that can actually be requested
    """
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
    """Make a cosmic login hash from a username and a password.

    Args:
        username (str): The username to login with
        password (str): The password to login with

    Returns:
        str: The auth_hash that can be used in URL requests.
    """
    # Cosmic are idiots, so they actually expect a newline in the encoded str
    # What the actual fuck.
    hash = base64.b64encode(f"{username}:{password}\n".encode("UTF-8")).decode("UTF-8")
    log.info(f"Computed hash: {hash}")
    return hash


pqdm = functools.partial(tqdm, disable=log.getEffectiveLevel() > 20)
"""An instance of tqdm, but that shuts off when the log level is higher than INFO"""


@dataclass
class EnsemblID:
    """Class representation of an ensembl ID"""

    full_id: str
    full_id_no_version: str
    type: str
    type_letter_prefix: str
    identifier: int
    version_number: Optional[int]


ENS_ID_MATCHER = re.compile("ENS(FM|GT|[EGPRT])([0-9]{11})(?:.([0-9]+))?")
"""RE to match any ensembl ID and deconstruct it"""


def split_ensembl_ids(ensembl_id: str) -> EnsemblID:
    """Splits an ensembl ID string into its components

    Args:
        ensembl_id (str): The ensembl id to split
    Returns:
        EnsemblID: The deconstructed ID
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

    return EnsemblID(
        full_id=ensembl_id,
        full_id_no_version=f"ENS{match.groups()[0]}{match.groups()[1]}",
        type=type,
        type_letter_prefix=match.groups()[0],
        identifier=int(match.groups()[1]),
        version_number=ver,
    )


def tolerant_is_nan(item: Any) -> bool:
    """Checks if the passed item is NaN with math.isnan() but does not fail if item is not a number"""
    try:
        return math.isnan(item)
    except TypeError:
        return False


def represent_sql_type(data: pd.Series) -> list[str]:
    """Convert a series to their SQL representations

    Converts NaNs and NAs to NULLs, and escapes and wraps in quotes strings.

    Args:
        data (pd.Series): The series to convert

    Returns:
        list[str]: The list of represented items from the series
    """
    result = []

    for item in data:
        if pd.isnull(item) or tolerant_is_nan(item) or item == np.NaN:
            result.append("NULL")
        elif isinstance(item, Number):
            result.append(str(item))
        elif isinstance(item, str) and item == "NA":
            result.append("NULL")
        elif isinstance(item, str):
            result.append("'" + item.replace("'", "''") + "'")
        elif isinstance(item, bool):
            result.append(int(item))

    return result


def to_transaction(data: pd.DataFrame, table: str) -> str:
    """Convert a dataframe to a SQL statement inserting the data in the frame to a database

    Like pd.DataFrame.to_sql() but without the schema (I want to do that manually beforehand).
    The conversion will:
        - Remove all-NULL lines.
        - Remove duplicated lines (you will never want them in the DB anyway)
        - Collapse NAs and NaNs to NULLs

    Args:
        data (pd.DataFrame): The data to convert
        table (str): The name of the table to insert the data to

    Returns:
        str: The SQL statement, ready for execution.
    """
    log.info(
        f"Converting a {data.shape[0]} rows by {data.shape[1]} cols dataframe to a transaction string..."
    )

    sql = ["INSERT INTO " + table + " (" + ", ".join(data.columns) + ") VALUES "]
    for _, row in pqdm(data.iterrows(), total=data.shape[0]):
        if all(lmap(lambda x: pd.isnull(x) or tolerant_is_nan(x), row.values)):
            # This row is all NULLs. Skip it
            continue
        sql.append("(" + ", ".join(represent_sql_type(row.values)) + "),")
    sql = "\n".join(sql)
    sql = sql.strip()[:-1]  # remove the trailing \n and the last comma
    sql = sql + ";"
    return sql


def sanity_check(check: bool, message: str):
    """Run a sanity check - an assertion but with log messages.

    Raises Abort if the check fails.

    Args:
        check (bool): The check to test
        message (str): The 'error' message
    """
    log.debug(f"Sanity check: {message}")
    if not check:
        log.critical(f"SANITY CHECK FAILED: {message}")
        raise Abort


def lmap(*args, **kwargs) -> list:
    """A not-lazy map."""
    return list(map(*args, **kwargs))


def execute_transaction(connection, transaction):
    """Run a transaction on a connection. With logging!"""
    log.info("Executing transaction...")
    connection.execute(transaction)


def print_duplicates(data: pd.DataFrame) -> None:
    """Debug function to print out duplicated rows of a dataframe."""
    print(data[~data.duplicated(keep=False)])


## -- This whole block is useless as of right now.
# The ensembl hugo symbol descriptions come with these extra data
# The idea was to split them, to remove them, and at the same time check that
# we were associating them to the correct symbol-accession pairs.
# However, not all descriptions are of hugo symbols with these extra data, so
# the idea was scrapped.
# I keep the code here if someday we want to use extra logic to handle entries
# without this data.
GENE_DESC_MATCHER = re.compile("^(.*?)\\[Source:(.*?);Acc:(.*?)\\]$")
"""RE to match gene description strings."""


@dataclass
class GeneDescription:
    """Dataclass representing the description of a gene."""

    original: str
    desc: str
    source: str
    accession: str


def split_gene_description(desc) -> GeneDescription:
    """Split a description string into a GeneDescription object"""
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
    """Helper to select and rename columns in a dataframe

    Args:
        data (pd.DataFrame): The dataframe to recast.
        mold (dict): A dict of {'old_col': 'new_col'} key-value pairs.

    Returns:
        pd.DataFrame: The recast dataframe
    """
    relevant: pd.DataFrame = data[list(mold.keys())]
    return relevant.rename(columns=mold)


def expand_column(data: pd.DataFrame, col: str, sep: str) -> pd.DataFrame:
    """Expand a compressed dataframe column to new rows

    For each row in the dataframe, the function splits the content of the col
    by the sep, and explodes the result to new line, one for each splitted value.

    Drops duplicated rows after the explosion.

    Args:
        data (pd.DataFrame): The dataframe to operate upon
        col (str): The column name to operate upon
        sep (str): The separator to split by

    Returns:
        pd.DataFrame: The exploded dataframe
    """

    def split_strings(x):
        if isinstance(x, str):
            return x.split(sep)
        else:
            return x

    data[col] = lmap(lambda x: split_strings(x), data[col])

    return data.explode(col).drop_duplicates()


@dataclass
class TcId:
    """Dataclass representing a Transporter Classification Database ID"""

    type: str
    subtype: str
    family: str
    subfamily: str
    full: str


def split_tcdb_ids(tcdb_id: str) -> TcId:
    """Split a TCDB ID to its component parts

    Args:
        tcdb_id (str): The ID to split

    Returns:
        TcId: The splitted TCDB ID object
    """
    parts = tcdb_id.split(".")

    assert len(parts) == 5, f"Invalid TCDB id ({tcdb_id}). Is it complete?"

    obj = TcId(
        type=str(parts[0]),
        subtype=".".join(parts[0:2]),
        family=".".join(parts[0:3]),
        subfamily=".".join(parts[0:4]),
        full=tcdb_id,
    )

    return obj


@dataclass
class RefseqId:
    """Dataclass representing a RefSeq ID."""

    full: str
    id: str
    version: str


def split_refseq_ids(refseq_id: str) -> RefseqId:
    """Split a RefSeq ID to its component parts.

    It only accepts full IDs (with the version). Version-less ID splitting makes
    little sense.

    Args:
        refseq_id (str): The refseq ID to split

    Returns:
        RefseqId: The splitted refseq ID object
    """
    parts = refseq_id.split(".")

    assert len(parts) == 2, f"Invalid Refseq ID {refseq_id}. Is it complete?"

    return RefseqId(full=refseq_id, id=parts[0], version=parts[1])


def merge_lists(lst1: list, lst2: list) -> list:
    """Extend one list by another.

    Robust if one of the two inputs are not actually lists.
    """
    if not isinstance(lst1, list):
        lst1 = [lst1]
    if not isinstance(lst2, list):
        lst2 = [lst2]
    lst1.extend(lst2)
    return lst1


# A very bad flattening function
def flatten(l):
    out = []
    for item in l:
        if isinstance(item, (list, tuple)):
            out.extend(flatten(item))
        else:
            out.append(item)
    return out


def get_local_csv(file_name: str) -> pd.DataFrame:
    """Get a local data file based on its file name.

    The local data has to live in the ./manual_data folder and be a .csv file.

    Args:
        file_name (str): The name of the file to load.

    Returns:
        A `pd.DataFrame` with the loaded data.
    """
    with resources.open_text(local_data, file_name) as file:
        return pd.read_csv(file)


def get_local_bytes(file_name: str) -> BytesIO:
    with resources.files(local_data).joinpath(file_name).open("rb") as file:
        return BytesIO(file.read())


def get_local_text(file_name: str) -> StringIO:
    with resources.files(local_data).joinpath(file_name).open(
        "r", encoding="UTF-8"
    ) as file:
        return StringIO(file.read())


def get_local_post_build_hooks() -> dict[str:StringIO]:
    local_hooks = {}
    for file in resources.files(post_build_hooks).iterdir():
        if file.is_file() and file.name.lower().endswith(".sql"):
            with file.open("r", encoding="UTF-8") as stream:
                local_hooks[file.name] = StringIO(stream.read())

    # Sort the hooks by file name and return them as a sorted list
    # This seems like black magic, but it works!
    local_hooks = dict(sorted(local_hooks.items()))
    return local_hooks


def explode_on(
    data: pd.DataFrame, on: str, columns: Optional[list[str]] = None
) -> pd.DataFrame:
    """Explode a dataframe.

    In all `columns`, split the value on the string `on`, then call `.explode()`
    on the result.

    Args:
        data (pd.DataFrame): The data to explode.
        on (str): The string to use to split
        columns (Optional[list[str]], optional): Optional list of columns to act
        upon. If unspecified, uses all of them. Defaults to None.

    Returns:
        pd.DataFrame: The exploded data
    """

    # This works very, very badly, but seems to work
    original_cols = data.columns
    if not columns:
        columns = list(original_cols)

    def conservative_split(x):
        if isinstance(x, str):
            return x.split(on)
        else:
            return [x]

    def to_list(x):
        if isinstance(x, list):
            return x
        return [x]

    for col in columns:
        data[col] = lmap(conservative_split, data[col])

    # lists in the cols may have different lengths, but as long as they are all
    # either the max or 1, we can still explode

    new_rows = []
    for _, row in data.iterrows():
        row = lmap(to_list, row)

        lengths = lmap(len, row)
        max_len = max(lengths)

        assert all(
            lmap(lambda x: x == 1 or x == max_len, lengths)
        ), f"Cols have incompatible split lengths (row {row})"

        mults = [max_len if x == 1 else 1 for x in lengths]

        row = [x * y for x, y in zip(row, mults)]

        new_rows.append(row)

    data = pd.DataFrame(new_rows, columns=original_cols)

    data = data.explode(column=list(original_cols), ignore_index=True)

    return data.drop_duplicates()


def apply_thesaurus(frame: pd.DataFrame, col="carried_solute") -> pd.DataFrame:
    """Apply the thesaurus on a dataframe,

    Optionally specify which col has the carried solute information

    Args:
        frame (pd.DataFrame): The frame to act upon
        col (str, optional): The col to act upon. Defaults to "carried_solute".

    Returns:
        pd.DataFrame: The (exploded) frame with the synonyms
    """
    thesaurus = get_local_csv(THESAURUS_FILE)
    # First, replace every entry with its "change_to" equivalent
    change_to = thesaurus.dropna(axis=0, subset="change_to")

    rows, _ = frame.shape

    log.info("Applying thesaurus equivalences...")
    for _, line in change_to.iterrows():
        frame.loc[frame[col] == line["original"], col] = line["change_to"]

    log.info("Adding thesaurus synonyms...")
    synonyms = thesaurus.dropna(axis=0, subset="synonyms")
    for _, line in synonyms.iterrows():
        frame.loc[
            frame[col] == line["original"], col
        ] = f"{line['original']},{line['synonyms']}"

    new_frame = explode_on(frame, ",", [col])

    log.info(f"New thesaurus rows: {new_frame.shape[0] - rows}")

    return new_frame
