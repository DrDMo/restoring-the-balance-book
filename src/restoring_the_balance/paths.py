"""Repository path constants.

Importing from a single source keeps notebooks, scripts, and tests in
agreement about where data and figure outputs live, regardless of the
caller's working directory.

Raw and intermediate data never live in this repository. Point the
``RTB_DATA_ROOT`` environment variable at a local folder that contains
``raw/`` (the series source files) and ``processed/`` (intermediate files).
Without it, ``<repo>/Data`` is used, which is git-ignored.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = Path(os.environ.get("RTB_DATA_ROOT", REPO_ROOT / "Data"))
RAW_DIR: Path = DATA_DIR / "raw"
PROC_DIR: Path = DATA_DIR / "processed"
FIGURES_DIR: Path = REPO_ROOT / "figures"
TABLES_DIR: Path = REPO_ROOT / "results" / "tables"
NOTEBOOKS_DIR: Path = REPO_ROOT / "notebooks"
SCRIPTS_DIR: Path = REPO_ROOT / "scripts"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
