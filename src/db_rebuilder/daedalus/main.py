"""This module holds the main function, that handles argument parsing and more."""

import argparse
import logging
import os
from pathlib import Path
from time import sleep

from daedalus.constants import CACHE_NAME, DB_NAME, DESCRIPTION, EPILOG
from daedalus.errors import Abort
from daedalus.make_db import generate_database
from daedalus.utils import make_cosmic_hash

log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        prog="daedalus",
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "out_dir",
        help=(
            "A directory to save the database and cache to."
            " Will create parent folders as needed."
        ),
        type=Path,
    )
    parser.add_argument(
        "cosmic_email",
        help="COSMIC database username (email). If omitted, will not include COSMIC data.",
        default=None,
        nargs="?",
    )
    parser.add_argument(
        "cosmic_password",
        help="COSMIC database password. If omitted, will not include COSMIC data.",
        default=None,
        nargs="?",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Increase verbosity"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="If passed, daedalus is allowed to overwrite an existing database.",
    )
    parser.add_argument(
        "--regen-cache",
        action="store_true",
        help="If passed, deletes the cache (if found) before running, regenerating it.",
    )
    parser.add_argument(
        "--skip",
        help="Comma-delimited string of runners to skip. Will fail if passed with --run.",
    )
    parser.add_argument(
        "--run",
        help="Comma-delimited string of runners to run. Will fail if passed with --skip.",
    )

    args = parser.parse_args()

    # The fact that you have to be logged in to download COSMIC data
    # is pretty retarded - but hey, who am I to judge the Sanger institute?
    if args.cosmic_email and args.cosmic_password:
        cosmic_hash = make_cosmic_hash(args.cosmic_email, args.cosmic_password)
    else:
        cosmic_hash = None
        log.warn(
            (
                "Missing or partial username/password combination."
                " Will NOT populate COSMIC tables."
                " If you need an account, you can register @ https://cancer.sanger.ac.uk/cosmic/"
                " Resuming execution in 2 seconds..."
            )
        )
        sleep(2)

    # Make the path to the output dir
    out_dir: Path = args.out_dir  # Just to help with type hints
    if not out_dir.exists():
        log.info(f"Making path to {out_dir}...")
        os.makedirs(out_dir, exist_ok=True)

    if not args.overwrite and (out_dir / DB_NAME).exists():
        raise Abort(
            (
                f"Database '{out_dir / DB_NAME}' exists."
                " Will not overwrite."
                " (Pass --overwrite to override this)."
            )
        )

    if (out_dir / DB_NAME).exists() and args.overwrite:
        # The "and args.overwrite" is redundant, but just to be safe...
        log.info("Removing existing database...")
        os.remove(out_dir / DB_NAME)

    if out_dir.exists() and (out_dir / CACHE_NAME).exists() and args.regen_cache:
        log.info("Removing existing data cache...")
        os.remove(out_dir / CACHE_NAME)

    log.info("Generating database...")

    to_run = args.run.split(",") if args.run else []
    to_skip = args.skip.split(",") if args.skip else []

    try:
        generate_database(
            path=out_dir, auth_hash=cosmic_hash, to_run=to_run, to_skip=to_skip
        )
    except Abort:
        log.error("Abort!")
        return

    log.info("Done!")
