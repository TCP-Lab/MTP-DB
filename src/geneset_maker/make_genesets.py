#!/usr/bin/env python3
from __future__ import annotations

"""This script makes gene lists apt for GSEA from the db"""
import json
import logging
import os
from collections import Counter
from copy import copy
from enum import Enum
from logging import StreamHandler
from pathlib import Path
from sqlite3 import Connection, connect
from typing import Any, Optional
from uuid import uuid4 as id

import pandas as pd
from colorama import Back, Fore, Style


class PruneDirection(Enum):
    TOPDOWN = "topdown"
    BOTTOMUP = "bottomup"


class IntegrityError(Exception):
    pass


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

    def subset(self, node_id, preserve_data=True) -> Tree:
        """Get just a branch from this tree as a new tree"""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found.")

        new_nodes = {}
        for node in copy(self.nodes).values():
            if node.id == node_id:
                # This is the new root node
                node.id == "0"
                if not preserve_data:
                    node.data = None
                new_nodes[node.id] = node

            if self.has_ancestor(node.id, node_id):
                if node.parent == node_id:
                    node.parent = "0"
                new_nodes[node.id] = node

        new_tree = Tree()
        new_tree.nodes = new_nodes
        new_tree.check_integrity()

        return new_tree

    def has_ancestor(self, node_id, ancestor_node_id) -> bool:
        """Test if ancestor_node is a parent of node_id"""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found.")

        if ancestor_node_id == "0":
            return True
        if node_id == "0":
            return False

        parent = self.get_parent(node_id)
        while parent.parent is not None:
            if parent.id == ancestor_node_id:
                return True
        return False

    def paste(
        self,
        other_tree: Tree,
        node_id: str,
        other_node_id: str = "0",
        update_data: bool = False,
    ):
        """Paste a node of another tree to a node in this tree"""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} in original tree not found.")

        other_tree = other_tree.subset(other_node_id)

        # if we need to update this node with the other tree's root node,
        # we can do it here
        paste_node = self.nodes[node_id]
        if update_data:
            paste_node.data = other_tree.nodes["0"].data

        # Update the parent IDs of children in the other tree to the new root
        # id
        new_nodes = {paste_node.id: paste_node}
        for node in other_tree.nodes.values():
            if node.parent == "0":
                node.parent = node_id
            new_nodes[node.id] = node

        # Add the new tree to the current tree
        self.nodes.update(new_nodes)

        self.check_integrity()

    def check_integrity(self):
        """Check if the tree is still valid"""
        possible_values = list(self.nodes.keys())
        found_root = False
        for node in self.nodes.values():
            if node.parent is None and not found_root:
                found_root = True
                continue
            elif node.parent is None and found_root:
                raise IntegrityError("Found two roots in the tree.")

            if node.parent not in possible_values:
                raise IntegrityError(f"Node {node} failed to validate.")

        return True

    def get_node_from_name(self, name: str) -> Node:
        """Get a node from a name.

        Raises ValueError if more than one node shares the same name
        """
        candidates = [x for x in self.nodes.values() if x.name == name]

        if len(candidates) > 1:
            candidates = [str(x) for x in candidates]
            raise ValueError(
                f"More than one node shares the same name '{name}': {candidates}"
            )

        if len(candidates) == 0:
            candidates = [str(x) for x in candidates]
            raise ValueError(f"No node found for query '{name}': {candidates}")

        return candidates[0]

    def is_leaf(self, node_id) -> bool:
        """Return if a given node is a leaf"""
        if node_id not in self.nodes:
            ValueError(f"Node {node_id} not found.")

        for node in self.nodes.values():
            if node.parent == node_id:
                return False
        return True

    def leaves(self) -> list[Node]:
        """Get a list of all the leaves in the tree"""
        leaves = [node for node in self.nodes.values() if self.is_leaf(node.id)]

        return leaves

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

    def depth_of(self, node_id) -> Node:
        assert node_id in self.nodes, f"Cannot find {node_id} in the tree"
        if node_id == "0":
            return 0
        i = 1
        parent = self.get_parent(node_id)
        while parent is not None:
            parent = self.get_parent(parent.id)
            i += 1
        return i

    def __str__(self) -> str:
        return f"Tree with {len(self.nodes)} nodes"


def prune(tree: Tree, similarity: float, direction: PruneDirection) -> Tree:
    original_len = len(tree.nodes)
    log.info(f"Pruning {tree}.")

    reverse_sort = direction == PruneDirection.BOTTOMUP

    def is_similar(node: Node, nodes: list[Node]) -> bool:
        for other in nodes:
            if any([other.id == "0", node.id == "0"]):
                continue
            if (
                len(set(other.data) ^ set(node.data))
                / len(set(other.data) | set(node.data))
                > similarity
            ):
                continue
            return True
        return False

    cycle = 0
    pruned = True
    while pruned:
        pruned = False
        log.info(f"Prune cycle {cycle} -- {len(tree.nodes)} nodes.")
        # Find all leaves
        leaves = tree.leaves()

        # Sort them
        leaves.sort(key=lambda x: tree.depth_of(x.id), reverse=reverse_sort)

        # Prune
        for node in leaves:
            other_nodes = list(copy(list(tree.nodes.values())))
            other_nodes.remove(node)
            if is_similar(node, other_nodes):
                log.debug(f"Pruned {node}")
                pruned = True
                tree.prune(node.id)

        cycle += 1

    len_diff = original_len - len(tree.nodes)
    log.info(
        f"Prune finished. Removed {len_diff} nodes - {round(len_diff / original_len * 100, 4)} %"
    )

    return tree


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
    trees = {}
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
        trees[name] = tree

    # 3. Make the union of the genesets following the structure
    log.info("Pasting trees together...")
    large_tree = Tree()
    for source, sink in sets["structure"]:
        large_tree.paste(
            trees[sink],
            large_tree.get_node_from_name(source).id,
            other_node_id=trees[sink].get_node_from_name(sink).id,
            update_data=True,
        )
        print(large_tree)

    if not args.no_prune:
        log.info("Pruning tree...")
        large_tree = prune(
            large_tree,
            similarity=args.prune_similarity,
            direction=PruneDirection(args.prune_direction),
        )

    to_files(large_tree, args.out_dir)

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
    parser.add_argument(
        "--no_prune", help="Do not run pruning on the gene lists", action="store_true"
    )
    parser.add_argument(
        "--prune_similarity",
        type=float,
        help="Node similarity threshold for pruning",
        default=0.1,
    )
    parser.add_argument(
        "--prune_direction",
        choices=["topdown", "bottomup"],
        help="Direction to prune nodes in",
        default="topdown",
    )
    parser.add_argument("--verbose", help="Increase verbosity", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    main(args)
