#!/usr/bin/env python3

"""This script makes gene lists apt for GSEA from the db"""
import json
import logging
import os
from collections import Counter
from copy import copy
from logging import StreamHandler
from pathlib import Path
from sqlite3 import Connection, connect
from typing import Any, Optional
from uuid import uuid4 as id

import pandas as pd
from colorama import Back, Fore, Style


class Node:
    def __init__(
        self, parent: str, name: Optional[str] = None, data: Any = None
    ) -> None:
        assert isinstance(parent, str), "Parent node must be a string!"
        self.id = str(id())
        self.name = name or self.id
        self.data = data
        self.parent = parent

    def __str__(self) -> str:
        base = f"Node '{self.name}' <{self.id}>"
        if self.data:
            base += f" + data"
        if self.parent:
            base += f" parent: <{self.parent}>"

        return base


class Tree:
    def __init__(self) -> None:
        root = Node("", "root")
        root.parent = None
        root.id = "0"
        self.nodes = {root.id: root}

    def all_nodes(self):
        """Get an iterator to all node_id: node pairs"""
        return copy(self.nodes).items()

    def create_node(self, name, parent="0", data=None):
        if parent not in self.nodes:
            raise ValueError(f"Cannot find parent node {parent} in current tree")

        node = Node(parent=parent, name=name, data=data)
        self.nodes[node.id] = node

        return node.id

    def paste(self, other_tree, node_id, update_data=False):
        """Paste the root of another tree to a leaf node in this tree"""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} in original tree not found.")

        if not self.is_leaf(node_id):
            # If we fuse roots, no child nodes need to be updated to the new ID
            raise ValueError(f"Node {node_id} is not a leaf. Cannot paste.")

        # Copy the current leaf node data to the root of the other tree
        leaf_node = self.nodes[node_id]
        if update_data:
            leaf_node.data = other_tree.nodes["0"].data

        # Update the parent IDs of children in the other tree to the new root
        # id
        new_nodes = {leaf_node.id: leaf_node}
        for node in other_tree.nodes.values():
            if node.parent == "0":
                node.parent = node_id
            new_nodes[node.id] = node

        # Drop the current leaf node
        self.prune(node_id)

        # Add the new tree to the current tree
        self.nodes.update(new_nodes)

    def is_leaf(self, node_id) -> bool:
        """Return if a given node is a leaf"""
        if node_id not in self.nodes:
            ValueError(f"Node {node_id} not found.")

        for node in self.nodes.values():
            if node.parent == node_id:
                return False
        return True

    def update_data(self, node_id, new_data):
        """Update the data of a given node"""
        if node_id not in self.nodes:
            ValueError(f"Node {node_id} not found.")

        self.nodes[node_id].data = new_data

    def update_name(self, node_id, new_name):
        """Update the name of a given node"""
        if node_id not in self.nodes:
            ValueError(f"Node {node_id} not found.")

        self.nodes[node_id].name = new_name

    def prune(self, node_id):
        """Remove the node and all sub-nodes that are children of the pruned node"""
        if node_id not in self.nodes:
            ValueError(f"Node {node_id} not found.")

        self.nodes.pop(node_id)
        for id, node in self.all_nodes():
            if node.parent == node_id:
                self.prune(id)

    def get_parent(self, node_id) -> Node:
        """Get the parent of a node"""
        assert node_id in self.nodes, f"Cannot find {node_id} in the tree"
        if node_id == "0":
            return None
        return self.nodes[self.nodes[node_id].parent]

    def get_paths(self) -> list[tuple[str]]:
        """Get a list of paths from the root node to all other nodes"""
        paths = []

        # For every node, get the full path to the parent.
        for node in self.nodes.values():
            path = []
            current_id = node.id
            while True:
                path.append(current_id)
                if current_id == "0":
                    # This is the root node, we are at the root
                    break
                # This node should have a parent
                current_id = self.get_parent(current_id).id
            path.reverse()
            paths.append(path)

        return paths

    def __str__(self) -> str:
        return f"Tree with {len(self.nodes)} nodes"


def to_files(trees: Tree, out_dir: Path):
    i = 0
    for tree in trees:
        with (out_dir / f"all{i}.txt").open("w+") as stream:
            stream.writelines([f"{x}\n" for _, x in tree.all_nodes()])

        paths = tree.get_paths()

        for path in paths:
            names = [tree.nodes[x].name for x in path]
            names.insert(0, out_dir)
            real_path = Path(*names)
            if not real_path.exists():
                log.info(f"Making {real_path}...")
                os.makedirs(real_path, exist_ok=True)
            with (real_path / "data.txt").open("w+") as stream:
                data = tree.nodes[path[-1]].data
                if data:
                    stream.writelines([f"{x}\n" for x in data])
        i += 1


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

    log.info(f"Connecting to {args.database_path}...")
    connection: Connection = connect(args.database_path)

    # 1. Generate large tables
    log.info("Making large tables...")
    with args.basic_gene_lists.open("r") as stream:
        sets = json.load(stream)

    large_tables = make_large_tables(connection, sets)

    log.info(f"Made {len(large_tables)} large tables.")

    # 2. Generate lists from large tables
    log.info("Generating gene trees...")
    trees = []
    for name, table in large_tables.items():
        log.info(f"Processing table {name}")
        tree = generate_gene_list_trees(
            table,
            name,
            min_pop_score=args.min_pop_score,
            min_set_size=args.min_set_size,
            min_recurse_set_size=args.min_recurse_set_size,
            recurse=not args.no_recurse,
        )
        trees.append(tree)

    to_files(trees, args.out_dir)

    log.info("Finished!")


def make_large_tables(conn: Connection, sets: dict) -> dict[pd.DataFrame]:
    """Generate large tables from a database and a list of genesets

    The database is seen as a series of tables that have to be row-wise joined
    to create larger tables to be queried for gene sets.

    The number and way to combine these tables is given by the `sets` param.

    Args:
        conn (Connection): A connection to the database
        sets (dict): A dictionary with two keys: "genesets" and "queries".
            The "genesets" key has to have a dictionary with as keys the names
            of the large tables, and as values list of table names from the
            database that have to be joined together to form a large table.
            The "queries" key has to have a dictionary with as keys table names
            of the database and as values SQL queries that return the table in
            question for joining.
            Tables in "genesets" that are not in "queries" will be retrieved
            with "SELECT * FROM {table_name};"

    Returns:
        dict[pd.DataFrame]: A dictionary with the same keys as the
            sets["genesets"] dictionary and as values pandas DataFrames with
            the resulting data.
    """
    assert type(sets.get("genesets", None)) == dict, "Genesets dictionary not found."
    # Test if the specified table names are available
    possible_tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    ).fetchall()
    possible_tables = list(map(lambda x: x[0], possible_tables))

    queries = sets.get("queries", None)

    large_tables = {}
    for set_name, tables in sets["genesets"].items():
        assert all(map(lambda x: x in possible_tables, tables)), "Invalid input tables"

        loaded_tables = []
        for table_name in tables:
            query = (
                queries[table_name]
                if queries and table_name in queries
                else f"SELECT * FROM {table_name};"
            )
            log.debug(f"Loading table {table_name} with query {query}.")
            loaded_tables.append(pd.read_sql(query, conn))

        large_tables[set_name] = pd.concat(loaded_tables, ignore_index=True, sort=False)

    return large_tables


def generate_gene_list_trees(
    dataframe: pd.DataFrame,
    name: str,
    id_col: str = "ensg",
    min_pop_score: float = 0.5,
    min_set_size: int = 10,
    min_recurse_set_size: int = 40,
    recurse: bool = True,
) -> Tree:
    """Generate gene lists from a dataframe.

    Takes a dataframe with at least the ID_COL, then uses the other columns to
    generate possible gene lists with.

    Args:
        dataframe (pd.DataFrame): The dataframe to source
        id_col (str, optional): The column to use as IDs. Defaults to "ensg".
        min_pop_score (float, optional): Minimum percentage of non-NA values in
          a column to be considered for gene lists. Defaults to 0.5.
        min_set_size (int, optional): Minimum number of genes to produce a valid
          gene set. Defaults to 10.
        min_recurse_set_size (int, optional): If recurse is true, minimum parent
          gene set size to have before running recursion on it.
        recurse (bool, optional): Recurse of sub-dataframes? Defaults to TRUE
        name (str, optional): The name to give to the overall set of genesets.
          in other words, the name of the parent node for this geneset.

    Returns:
        Tree: A Tree structure of nodes, where each node contains the geneset
    """

    def generate_list(frame: pd.DataFrame, layer: int):
        log.info(f"Enumerating layer {layer}: {list(frame.columns)}")
        # This is the recursive wrapper
        tree = Tree()

        valid_cols = []
        for current_col in list(frame.columns):
            if sum(frame[current_col].isna()) / len(frame.index) > min_pop_score:
                log.debug(f"Layer {layer} -- col {current_col} ... SKIPPED (too empty)")
                continue
            valid_cols.append(current_col)

        iter_cols = valid_cols  # Remove ID col
        iter_cols.remove("ensg")
        for current_col in iter_cols:
            # Skip processing of id col
            if current_col == id_col:
                continue
            counts = Counter(frame[current_col].dropna())

            for value in set(counts.elements()):
                if counts[value] < min_set_size:
                    log.debug(
                        f"Layer {layer} -- col {current_col} -- value {value} ... SKIPPED (too small)"
                    )
                    continue

                putative_list = (
                    frame[id_col][frame[current_col] == value]
                    .drop_duplicates()
                    .to_list()
                )

                # Skip if the putative gene set is too small
                if len(putative_list) < min_set_size:
                    log.debug(
                        f"Layer {layer} -- col {current_col} -- value {value} ... SKIPPED (too small pure set)"
                    )
                    continue

                node_name = f"{current_col}::{value}"
                node_id = tree.create_node(node_name, data=putative_list)

                if not recurse:
                    log.debug(
                        f"Layer {layer} -- col {current_col} -- value {value} ... ACCEPTED NR (id : {node_id})"
                    )
                    continue

                if len(putative_list) < min_recurse_set_size:
                    log.debug(
                        f"Layer {layer} -- col {current_col} -- value {value} ... ACCEPTED NR (id : {node_id})"
                    )
                    continue

                log.debug(
                    f"Layer {layer} -- col {current_col} -- value {value} ... ACCEPTED RC (id : {node_id})"
                )

                # Add back the ID col
                recurse_cols = list(frame.columns)
                recurse_cols.remove(current_col)
                new_data = dataframe.loc[dataframe[current_col] == value, recurse_cols]

                subtree = generate_list(new_data, layer=layer + 1)

                tree.paste(subtree, node_id)

        return tree

    all_colnames = list(dataframe.columns)
    # Remove the ID col
    all_colnames.remove(id_col)

    tree = Tree()
    tree_root = tree.create_node(
        name, data=dataframe[id_col].drop_duplicates().to_list()
    )

    subtree = generate_list(dataframe, 0)

    tree.paste(subtree, tree_root)

    log.debug(f"Generated {len(tree.all_nodes())} gene lists from table.")

    return tree


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
    parser.add_argument(
        "--min_recurse_set_size",
        type=int,
        default=40,
        help="Minimum size of set to recurse on",
    )
    parser.add_argument("--no_recurse", help="Suppress recursion", action="store_true")
    parser.add_argument("--verbose", help="Increase verbosity", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    main(args)
