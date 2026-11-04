"""Read the raw Cricsheet CSV2 files into two pandas DataFrames.

* parse_info_file / load_match_info: one row per match from <id>_info.csv
* load_deliveries: one row per ball from all_matches.csv

No cleaning happens here apart from types. Names are normalised in
tables.py so the raw values stay available for checking the alias maps.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from . import RAW_DIR

CSV_DIR = RAW_DIR / "csv2"

SINGLE_KEYS = {
    "season", "venue", "city", "toss_winner", "toss_decision", "winner",
    "winner_runs", "winner_wickets", "outcome", "eliminator", "method",
    "player_of_match", "match_number", "match_id",
}


def parse_info_file(path: Path) -> dict:
    """Turn one key/value style info file into a flat dict."""
    rec: dict = {"teams": [], "dates": [], "target_overs": None, "target_runs": None}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.reader(fh):
            if len(row) < 3 or row[0] != "info":
                continue
            key, vals = row[1], row[2:]
            if key == "team":
                rec["teams"].append(vals[0])
            elif key == "date":
                rec["dates"].append(vals[0])
            elif key == "target_overs" and len(vals) >= 2:
                rec["target_overs"] = float(vals[1])
            elif key == "target_runs" and len(vals) >= 2:
                rec["target_runs"] = int(vals[1])
            elif key in SINGLE_KEYS and key not in rec:
                rec[key] = vals[0]
    if not rec.get("match_id"):
        rec["match_id"] = path.name.split("_")[0]
    return rec


def load_match_info(csv_dir: Path = CSV_DIR) -> pd.DataFrame:
    files = sorted(csv_dir.glob("*_info.csv"))
    if not files:
        raise FileNotFoundError(f"no *_info.csv files in {csv_dir}, run `python -m ipl download`")
    rows = []
    for f in files:
        r = parse_info_file(f)
        teams = r.pop("teams")
        dates = r.pop("dates")
        r["team_a"], r["team_b"] = (teams + [None, None])[:2]
        # rescheduled games list two dates, the first is when play started
        r["start_date"] = sorted(dates)[0].replace("/", "-") if dates else None
        rows.append(r)
    df = pd.DataFrame(rows)
    df["match_id"] = df["match_id"].astype("int64")
    df["start_date"] = pd.to_datetime(df["start_date"])
    for col in ("winner_runs", "winner_wickets", "match_number"):
        df[col] = pd.to_numeric(df.get(col), errors="coerce")
    return df


def load_deliveries(csv_dir: Path = CSV_DIR) -> pd.DataFrame:
    path = csv_dir / "all_matches.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing, run `python -m ipl download`")
    df = pd.read_csv(path, low_memory=False, dtype={"season": "string"})
    for col in ("wides", "noballs", "byes", "legbyes", "penalty"):
        df[col] = df[col].fillna(0).astype("int64")
    df["start_date"] = pd.to_datetime(df["start_date"])
    return df
