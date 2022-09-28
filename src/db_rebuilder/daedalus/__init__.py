from pathlib import Path
import logging

OUT_ANCHOR: Path = Path("/app/out")

__all__ = ["OUTANCHOR"]
__version__ = "0.1.0"

DB_PATH = OUT_ANCHOR / f"MTPDB_v{__version__}.sqlite"

if DB_PATH.exists():
    raise Exception(f"Target DB already exists @{DB_PATH}. Aborting")

logging.basicConfig(level=logging.getLevelName("DEBUG"))

SCHEMA = "BEGIN;\n{}\nEND;".format(Path("/app/schema.sql").read_text())
