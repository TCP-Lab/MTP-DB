from pathlib import Path

from mazeinspector import DESC, USAGE
from mazeinspector.mazeinspector import main

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="MazeInspector", usage=USAGE, description=DESC
    )

    parser.add_argument("db_path", type=Path, help="Path to the database to inspect.")

    args = parser.parse_args()

    main(args)
