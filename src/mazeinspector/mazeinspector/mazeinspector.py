import sqlite3
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import tabulate as tb
from colorama import init
from tqdm import tqdm

from mazeinspector import __version__

init(autoreset=True)


def lmap(*args, **kwargs):
    return list(map(*args, **kwargs))


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
    type: Type
    emptiness: float
    possible_values: Optional[int]


@dataclass
class Table:
    name: str
    num_rows: int
    num_cols: int
    emptiness: float
    cols: list[TableColumn]

    @property
    def pretty(self) -> str:
        out = f"Table {self.name}\n"
        out += tb.tabulate(map(lambda x: x.__dict__, self.cols), headers="keys")

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
        except Exception as e:
            pass

    return Type.UNDEFINED


def calc_emptiness(values) -> float:
    nones = len([x for x in values if x is None])

    return nones / len(values)


def inspect_table(connection: sqlite3.Connection, table_name: str) -> Table:
    cursor = connection.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()
    cursor.close()
    colnames = select_i(cursor.description, 0)

    overall_emptiness = 0
    computed_cols = []
    for i, name in enumerate(colnames):
        values = select_i(data, i)

        clean_values = [x for x in values if x is not None]
        if clean_values:
            type = fuzzy_type_finder(clean_values)
        else:
            type = Type.NULL

        possible_values = set(values) if type is Type.FACTOR else None

        emptiness = calc_emptiness(values)
        overall_emptiness += emptiness

        computed_cols.append(
            TableColumn(
                name=name,
                type=type,
                emptiness=emptiness,
                possible_values=possible_values,
            )
        )

    return Table(
        name=table_name,
        emptiness=overall_emptiness / len(values),
        cols=computed_cols,
        num_cols=len(colnames),
        num_rows=len(values),
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

    table_objects = [inspect_table(conn, x) for x in tqdm(tables)]

    for t in table_objects:
        print(t.pretty + "\n")

    conn.close()
