"""Run the .sql files in ipl/sql against the DuckDB database."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from . import DB_PATH

SQL_DIR = Path(__file__).resolve().parent / "sql"


def load_sql(name: str) -> str:
    return (SQL_DIR / f"{name}.sql").read_text()


def run(name: str, db_path: Path = DB_PATH, **params) -> pd.DataFrame:
    """Run ipl/sql/<name>.sql. Keyword arguments fill $placeholders."""
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        return con.execute(load_sql(name), params or None).df()
    finally:
        con.close()


def query(sql: str, db_path: Path = DB_PATH, **params) -> pd.DataFrame:
    """Run an ad hoc SQL string (handy in the notebook)."""
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        return con.execute(sql, params or None).df()
    finally:
        con.close()
