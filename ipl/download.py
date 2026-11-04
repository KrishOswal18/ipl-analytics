"""Download and unpack the Cricsheet IPL archive (CSV2 format).

Cricsheet publishes every IPL match as two files: <id>.csv with one row per
delivery and <id>_info.csv with match metadata (toss, result, venue). The zip
also has all_matches.csv, which is every delivery stacked into one file.
"""

from __future__ import annotations

import shutil
import urllib.request
import zipfile
from pathlib import Path

from . import RAW_DIR

CRICSHEET_URL = "https://cricsheet.org/downloads/ipl_male_csv2.zip"
ZIP_NAME = "ipl_male_csv2.zip"
EXTRACT_DIR = "csv2"


def download(force: bool = False, raw_dir: Path = RAW_DIR) -> Path:
    """Fetch the zip (skipped if it already exists) and extract it.

    Returns the folder holding the extracted CSV files.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    zip_path = raw_dir / ZIP_NAME
    out_dir = raw_dir / EXTRACT_DIR

    if force or not zip_path.exists():
        print(f"Downloading {CRICSHEET_URL}")
        req = urllib.request.Request(CRICSHEET_URL, headers={"User-Agent": "ipl-analytics/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp, open(zip_path, "wb") as fh:
            shutil.copyfileobj(resp, fh)

    if not zipfile.is_zipfile(zip_path):
        raise RuntimeError(f"{zip_path} is not a zip file, delete it and retry")

    if force or not (out_dir / "all_matches.csv").exists():
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True)
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.namelist():
                # only flat .csv/.txt files are expected, refuse anything with a path
                name = Path(member).name
                if name != member or not name.endswith((".csv", ".txt")):
                    continue
                with zf.open(member) as src, open(out_dir / name, "wb") as dst:
                    shutil.copyfileobj(src, dst)
    n_info = len(list(out_dir.glob("*_info.csv")))
    print(f"Raw data ready in {out_dir} ({n_info} match info files)")
    return out_dir


if __name__ == "__main__":
    download()
