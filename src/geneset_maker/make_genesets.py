#!/usr/bin/env python3

"""This script makes gene lists apt for GSEA from the db"""
import json
import logging
from collections import Counter
from logging import StreamHandler
from pathlib import Path
from sqlite3 import Connection, connect

import pandas as pd
from colorama import Back, Fore, Style
from tqdm import tqdm


## >>>> Logging setup
class ColorFormatter(logging.Formatter):
    # Change this dictionary to suit your coloring needs!
    COLORS = {
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "DEBUG": Style.BRIGHT + Fore.MAGENTA,
        "INFO": Fore.GREEN,
        "CRITICAL": Style.BRIGHT + Fore.RED,
    }

    def format(self, record):
        reset = Fore.RESET + Back.RESET + Style.NORMAL
        color = self.COLORS.get(record.levelname, "")
        if color:
            record.name = Style.BRIGHT + Fore.CYAN + record.name + reset
            if record.levelname != "INFO":
                record.msg = color + record.msg + reset
            record.levelname = color + record.levelname + reset
        return logging.Formatter.format(self, record)


# Setup logging
# Dobby makes gene sets now!
log = logging.getLogger("Dobby")  # Keep this at the module level name
log.setLevel(logging.DEBUG)
log.propagate = False
# Keep this at DEBUG - set levels in handlers themselves

format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
console_formatter = ColorFormatter(format)

stream_h = StreamHandler()
stream_h.setFormatter(console_formatter)
stream_h.setLevel(logging.DEBUG)

log.addHandler(stream_h)
## <<<< Logging setup


def main(args: dict) -> None:
    log.info(f"Launching with args: {args}")

    log.info("Opening connection")
    connection: Connection = connect(args.database_path)
    # 1. Generate large tables
    log.info("Making large tables...")
    with args.basic_gene_lists.open("r") as stream:
        sets = json.load(stream)

    large_tables = make_large_tables(connection, sets)

    print(large_tables)

    # 2. Generate lists from large tables
    log.info("Generating gene lists...")
    gene_lists = {}
    for name, table in large_tables.items():
        gene_lists[name] = generate_gene_list(
            table, min_pop_score=args.min_pop_score, min_set_size=args.min_set_size
        )

    for table, lists in gene_lists.items():
        for name, list in lists.items():
            log.info("Writing lists to disk...")
            with (args.out_dir / f"{table}_{name}.txt").open("w+") as stream:
                stream.writelines([f"{x}\n" for x in list])


def make_large_tables(conn: Connection, sets: dict) -> dict[pd.DataFrame]:
    possible_tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    ).fetchall()
    possible_tables = list(map(lambda x: x[0], possible_tables))

    large_tables = {}
    for set_name, tables in sets.items():
        assert all(map(lambda x: x in possible_tables, tables)), "Invalid input tables"
        loaded_tables = [
            pd.read_sql(f"SELECT * FROM {table_name};", conn) for table_name in tables
        ]

        large_tables[set_name] = pd.concat(loaded_tables, ignore_index=True, sort=False)

    return large_tables


def generate_gene_list(
    dataframe: pd.DataFrame,
    id_col: str = "ensg",
    min_pop_score: float = 0.5,
    min_set_size: int = 10,
) -> list[str]:
    all_colnames = list(dataframe.columns)
    # Remove the ID col
    all_colnames.remove(id_col)
    df_len = len(dataframe.index)

    gene_lists = {"id": dataframe[id_col].drop_duplicates()}

    for column in all_colnames:
        log.debug(f"Considering col {column} for gene setting...")
        if sum(dataframe[column].isna()) / df_len > min_pop_score:
            log.debug("Column is too empty. Skipping...")
            continue

        log.debug("Enumerating...")
        coldata = dataframe[column].dropna()

        counts = Counter(coldata)
        for element in tqdm(counts.elements()):
            if counts[element] < min_set_size:
                continue
            putative_list = dataframe[id_col][
                dataframe[column] == element
            ].drop_duplicates()
            if len(putative_list) < min_set_size:
                continue
            gene_lists[f"{column}_{element}"] = putative_list

    log.info(f"Generated {len(gene_lists)} gene lists from table.")

    return gene_lists


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "database_path", type=Path, help="Database used as annotation source"
    )
    parser.add_argument(
        "basic_gene_lists", type=Path, help="Gene lists to draw from the database"
    )
    parser.add_argument("out_dir", type=Path, help="Output folder")

    parser.add_argument(
        "--min_pop_score",
        type=float,
        default=0.5,
        help="Minimum fraction of non-null values to consider cols",
    )
    parser.add_argument(
        "--min_set_size", type=int, default=10, help="Minimum generated set size"
    )

    args = parser.parse_args()

    main(args)
