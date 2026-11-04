"""IPL analytics pipeline built on Cricsheet ball-by-ball data."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
FIGURES_DIR = ROOT / "reports" / "figures"
WEB_DATA_DIR = ROOT / "web" / "public" / "data"
DB_PATH = PROCESSED_DIR / "ipl.duckdb"
