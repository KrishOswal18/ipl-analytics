"""Analysis layer: pulls tables from DuckDB, runs the SQL files and adds the
pandas-side features (consistency, rankings) that are awkward in SQL."""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from . import DB_PATH
from . import queries
from .features import consistency_metrics, rank_within, strike_rate, batting_average

MIN_BALLS_SEASON = 100     # batter qualifies for a season ranking
MIN_BALLS_CAREER = 500     # batter qualifies for all-time ranking
MIN_INNINGS_CONSISTENCY = 30
MIN_BOWL_BALLS_SEASON = 120
MIN_BOWL_BALLS_CAREER = 600
MIN_VENUE_MATCHES = 20


def table(name: str, db_path: Path = DB_PATH, columns: str = "*") -> pd.DataFrame:
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        return con.execute(f"SELECT {columns} FROM {name}").df()
    finally:
        con.close()


def batter_career(bat: pd.DataFrame) -> pd.DataFrame:
    """All-time batting with consistency metrics, for batters with enough balls."""
    rows = []
    for batter, g in bat.groupby("batter"):
        balls = int(g["balls"].sum())
        if balls < MIN_BALLS_CAREER:
            continue
        runs = int(g["runs"].sum())
        outs = int(g["out"].sum())
        cm = consistency_metrics(g["runs"])
        rows.append({
            "batter": batter,
            "team": g.groupby("batting_team")["balls"].sum().idxmax(),
            "seasons": int(g["season"].nunique()),
            "first_season": int(g["season"].min()), "last_season": int(g["season"].max()),
            "innings": cm["innings"], "runs": runs, "balls": balls, "dismissals": outs,
            "strike_rate": float(strike_rate(runs, balls)),
            "average": batting_average(runs, outs),
            "median_score": cm["median"], "cv": cm["cv"], "pct_25_plus": cm["pct_threshold"],
            "fours": int(g["fours"].sum()), "sixes": int(g["sixes"].sum()),
        })
    df = pd.DataFrame(rows)
    df["sr_rank"] = rank_within(df, "strike_rate")
    df["runs_rank"] = rank_within(df, "runs")
    # consistency index: share of 25+ scores, ranked among batters with enough innings
    qual = df["innings"] >= MIN_INNINGS_CONSISTENCY
    df["consistency_rank"] = pd.NA
    df.loc[qual, "consistency_rank"] = rank_within(df[qual], "pct_25_plus")
    return df.sort_values("runs", ascending=False).reset_index(drop=True)


def batter_season_consistency(bat: pd.DataFrame, min_innings: int = 8) -> pd.DataFrame:
    """Season level share of 25+ scores (used for per-season consistency boards)."""
    g = bat.groupby(["season", "batter"])
    df = g.agg(innings=("runs", "size"), runs=("runs", "sum"), balls=("balls", "sum"),
               pct_25_plus=("runs", lambda s: float((s >= 25).mean())),
               median_score=("runs", "median"),
               cv=("runs", lambda s: float(s.std(ddof=1) / s.mean()) if s.mean() > 0 and len(s) > 1 else np.nan)
               ).reset_index()
    return df[df["innings"] >= min_innings]


def bowler_career(bowl: pd.DataFrame) -> pd.DataFrame:
    g = bowl.groupby("bowler")
    df = g.agg(balls=("legal_balls", "sum"), runs_conceded=("runs_conceded", "sum"),
               wickets=("wickets", "sum"), dots=("dots", "sum"), innings=("match_id", "size"),
               seasons=("season", "nunique")).reset_index()
    team = bowl.groupby(["bowler", "bowling_team"])["legal_balls"].sum().reset_index()
    team = team.sort_values("legal_balls").groupby("bowler").tail(1).set_index("bowler")["bowling_team"]
    df["team"] = df["bowler"].map(team)
    df = df[df["balls"] >= MIN_BOWL_BALLS_CAREER].copy()
    df["economy"] = df["runs_conceded"] * 6 / df["balls"]
    df["dot_pct"] = df["dots"] / df["balls"]
    df["balls_per_wicket"] = df["balls"] / df["wickets"].replace(0, np.nan)
    df["economy_rank"] = rank_within(df, "economy", ascending=True)
    return df.sort_values("wickets", ascending=False).reset_index(drop=True)


def team_alltime(team_season: pd.DataFrame) -> pd.DataFrame:
    g = team_season.groupby("team")
    df = g.agg(seasons=("season", "nunique"), first_season=("season", "min"), last_season=("season", "max"),
               played=("played", "sum"), won=("won", "sum"), lost=("lost", "sum"),
               no_result=("no_result", "sum")).reset_index()
    df["win_pct"] = df["won"] / (df["won"] + df["lost"])
    return df.sort_values("win_pct", ascending=False).reset_index(drop=True)


def nrr_vs_winpct(team_season: pd.DataFrame) -> dict:
    """How tightly season NRR tracks season win %. Pearson r and a fitted line."""
    ts = team_season.dropna(subset=["nrr", "win_pct"])
    r = float(np.corrcoef(ts["nrr"], ts["win_pct"])[0, 1])
    slope, intercept = np.polyfit(ts["nrr"], ts["win_pct"], 1)
    return {"r": r, "r2": r * r, "slope": float(slope), "intercept": float(intercept), "n": int(len(ts))}


def load_all(db_path: Path = DB_PATH) -> dict:
    """Everything the notebook, charts and export need, in one dict."""
    out = {
        "matches": table("matches", db_path),
        "team_matches": table("team_matches", db_path),
        "batting_innings": table("batting_innings", db_path),
        "bowling_innings": table("bowling_innings", db_path),
        "season_summary": queries.run("season_summary", db_path),
        "team_season": queries.run("team_season", db_path),
        "venue_summary": queries.run("venue_summary", db_path, min_matches=MIN_VENUE_MATCHES),
        "venue_all": queries.run("venue_summary", db_path, min_matches=1),
        "batter_season": queries.run("batter_season", db_path, min_balls=MIN_BALLS_SEASON),
        "bowler_season": queries.run("bowler_season", db_path, min_balls=MIN_BOWL_BALLS_SEASON),
        "head_to_head": queries.run("head_to_head", db_path),
    }
    out["batter_career"] = batter_career(out["batting_innings"])
    out["batter_season_consistency"] = batter_season_consistency(out["batting_innings"])
    out["bowler_career"] = bowler_career(out["bowling_innings"])
    out["team_alltime"] = team_alltime(out["team_season"])
    out["dismissals"] = queries.query(
        "SELECT wicket_type, COUNT(*) AS n FROM deliveries "
        "WHERE wicket_type IS NOT NULL AND NOT is_super_over GROUP BY 1 ORDER BY 2 DESC", db_path)
    out["phase_by_era"] = queries.query(
        "SELECT CASE WHEN season <= 2012 THEN '2008-12' WHEN season <= 2017 THEN '2013-17' "
        "WHEN season <= 2022 THEN '2018-22' ELSE '2023-26' END AS era, phase, "
        "SUM(total_runs) * 6.0 / SUM(CASE WHEN is_legal THEN 1 END) AS run_rate, "
        "SUM(CASE WHEN is_wicket THEN 1 ELSE 0 END) * 1.0 / COUNT(DISTINCT match_id || '-' || innings) AS wickets_per_innings "
        "FROM deliveries WHERE NOT is_super_over GROUP BY 1, 2 ORDER BY 1, 2", db_path)
    return out
