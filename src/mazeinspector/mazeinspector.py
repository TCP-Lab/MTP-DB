import sqlite3
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import logging

import tabulate as tb
from colorama import init
from tqdm import tqdm

from mazeinspector import __version__

log = logging.getLogger(__name__)

init(autoreset=True)


def lmap(*args, **kwargs):
    return list(map(*args, **kwargs))

def pretty_print_dict(input: dict):
    out = ""
    for key, value in input.items():
        out += f"{key}: {value}\n"
    return out


class Type(Enum):
    STR = "string"
    INT = "integer"
    BOOL = "boolean"
    FLOAT = "float"
    FACTOR = "factor"
    NULL = "null"
    UNDEFINED = "unknown"


@dataclass
class TableColumn:
    name: str
    """The name of the column"""
    type: Type
    """The type of the column"""
    emptiness: float
    """The number of NULL values over the total rows"""
    relative_emptiness: float
    """The number of genes with NULL values over all genes
    
    This makes only sense with the 'ensg' column - it is the number of ensgs
    with NULL values over the total number of ensgs. In other words, the
    relative number of genes with this column set to NUL over all genes.
    """
    possible_values: Optional[int]
    """If this col is a factor, all levels of the factor"""


@dataclass
class Table:
    name: str
    """The name of the table"""
    num_rows: int
    """How many rows this table has"""
    num_cols: int
    """How many columns this table has"""
    emptiness: float
    """The number of NULL cells over all cells in this table"""
    cols: list[TableColumn]

    @property
    def pretty(self) -> str:
        out = f" ========== TABLE '{self.name}' ==========\n"
        out += tb.tabulate(map(lambda x: x.__dict__, self.cols), headers="keys")
        out += "\n\n~~~~~ Summary ~~~~~\n"
        out += f"Total cols: {self.num_cols}\n"
        out += f"Total rows: {self.num_rows}\n"
        out += f"Total cells: {self.num_rows * self.num_cols}\n"
        if self.emptiness is not None:
            out += f"Total emptiness: {round(self.emptiness * 100, 2)}%\n"

        return out


def select_i(iterable, i):
    return lmap(lambda x: x[i], iterable)


def all_in(iterable, test):
    return all([x in test for x in iterable])


def fuzzy_type_finder(data) -> Type:
    def test_bool(data):
        if all_in(lmap(int, data), (1, 0)):
            pass
        raise ValueError("This is not a boolean.")

    def test_factor(data):
        if len(set(lmap(str, data))) < round(len(data) ** 0.5, 0):
            pass
        raise ValueError("This is not a factor")

    def test_undefined(data):
        if all_in(lmap(str, data), ("None",)):
            pass
        raise ValueError("This does not look undefined")

    # The type hint is just there to remind you that the order is important here
    matches: OrderedDict = OrderedDict(
        {
            Type.NULL: test_undefined,
            Type.BOOL: test_bool,
            Type.INT: lambda x: lmap(int, x),
            Type.FLOAT: lambda x: lmap(float, x),
            Type.FACTOR: test_factor,
            Type.STR: lambda x: lmap(str, x),
        }
    )

    for type, test in matches.items():
        try:
            test(data)
            return type
        except ValueError:
            # All valueerrors are invalid tests, so we can just ignore them
            pass

    return Type.UNDEFINED


def calc_emptiness(values, total = None) -> float:
    if not values:
        raise ValueError(f"Cannot calculate emptiness on nothing: {values}")
    if not total:
        total = len(values)
    nones = len([x for x in values if x is None])

    return nones / total

def calc_relative_emptiness(cursor: sqlite3.Cursor, table_name: str, col_name: str) -> float:
    res = cursor.execute(f"SELECT DISTINCT ensg FROM {table_name} WHERE {col_name} IS NULL")
    data = res.fetchall()

    genes_with_missing_data = select_i(data, 0)

    return len(genes_with_missing_data) / len(get_ensgs(cursor, table_name))



def get_ensgs(cursor: sqlite3.Cursor, table_name: str) -> set[str]:
    res = cursor.execute(f"SELECT ensg FROM {table_name}")
    data = res.fetchall()
    
    return set(data)


def inspect_table(cursor: sqlite3.Cursor, table_name: str) -> Table:
    res = cursor.execute(f"SELECT * FROM {table_name}")
    data = res.fetchall()
    colnames = select_i(cursor.description, 0)

    overall_emptiness = 0
    max_len = 0
    computed_cols = []
    for i, name in enumerate(colnames):
        values = select_i(data, i)
        if not values:
            log.warn(f"No values are in the col {name} of table {table_name}. Skipping...")
            continue
        max_len = len(values) if len(values) > max_len else max_len

        clean_values = [x for x in values if x is not None]
        if clean_values:
            type = fuzzy_type_finder(clean_values)
        else:
            type = Type.NULL

        possible_values = set(values) if type is Type.FACTOR else None

        emptiness = calc_emptiness(values)
        if 'ensg' in colnames and name != 'ensg':
            relative_emptiness = calc_relative_emptiness(cursor, table_name=table_name, col_name=name)
        else:
            relative_emptiness = None
        overall_emptiness += emptiness * len(values)

        computed_cols.append(
            TableColumn(
                name=name,
                type=type,
                emptiness=emptiness,
                relative_emptiness=relative_emptiness,
                possible_values=possible_values,
            )
        )

    if max_len > 0:
        overall_emptiness = overall_emptiness / (max_len * len(colnames))
    else:
        # There are no values, they cannot be "empty"
        overall_emptiness = None
    
    cursor.close()

    return Table(
        name=table_name,
        emptiness=overall_emptiness,
        cols=computed_cols,
        num_cols=len(colnames),
        num_rows=max_len,
    )


def main(args):
    print(f"This is MazeInspector, version {__version__}")
    db_path = args.db_path.expanduser().absolute()
    print(f"Connecting to '{db_path}'")
    conn: sqlite3.Connection = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table';")
    tables = lmap(lambda x: x[0], cursor.fetchall())
    cursor.close()

    print(f"Found {len(tables)} tables in database. Starting inspection...")

    table_objects = [inspect_table(conn.cursor(), x) for x in tqdm(tables)]

    for t in table_objects:
        print(t.pretty + "\n")

    conn.close()
