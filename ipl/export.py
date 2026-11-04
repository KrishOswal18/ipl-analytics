"""Write the compact JSON files the static dashboard reads (web/public/data)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from . import WEB_DATA_DIR
from .normalise import ACTIVE_TEAMS, TEAM_ALIASES, TEAM_SHORT, VENUE_RENAMES

TOP_N = 30


def _clean(o):
    """Make numpy/pandas values JSON safe and round floats to keep files small."""
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_, bool)):
        return bool(o)
    if isinstance(o, (float, np.floating)):
        f = float(o)
        return None if math.isnan(f) or math.isinf(f) else round(f, 6)
    if o is pd.NA or o is None:
        return None
    if isinstance(o, pd.Timestamp):
        return o.strftime("%Y-%m-%d")
    return o


def _records(df: pd.DataFrame, cols: list[str]) -> list[dict]:
    return _clean(df[cols].to_dict(orient="records"))


def _write(name: str, obj, out_dir: Path) -> Path:
    p = out_dir / name
    p.write_text(json.dumps(_clean(obj), separators=(",", ":"), ensure_ascii=False))
    return p


def venue_by_season(matches: pd.DataFrame) -> dict:
    m = matches[matches["decided"]]
    out = {}
    for season, g in m.groupby("season"):
        v = g.groupby("venue").agg(
            matches=("match_id", "size"),
            chase_win_pct=("bat_first_won", lambda s: float(1 - s.mean())),
            avg_first_innings=("first_innings_runs", "mean"),
            toss_winner_win_pct=("toss_winner_won", "mean"),
            field_first_pct=("toss_decision", lambda s: float((s == "field").mean())),
        ).reset_index().sort_values("matches", ascending=False)
        out[str(season)] = _clean(v.to_dict(orient="records"))
    return out


def export(data: dict, toss: dict, wp: dict, cmp: dict, venue_toss: pd.DataFrame,
           counts: dict, out_dir: Path = WEB_DATA_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    ss = data["season_summary"]
    ts = data["team_season"]
    seasons = [int(s) for s in ss["season"]]

    summary = {
        "counts": counts,
        "seasons": seasons,
        "season_summary": _records(ss, [
            "season", "matches", "decided", "avg_first_innings", "field_first_pct",
            "toss_winner_win_pct", "chase_win_pct", "scores_200_plus", "rr_powerplay",
            "rr_middle", "rr_death", "rr_overall", "sixes_per_match"]),
        "toss": toss,
        "venue_toss": _records(venue_toss, ["venue", "wins", "n", "rate", "p_value", "p_bonferroni"]),
        "nrr_fit": data["nrr_fit"],
        "champions": _records(data["matches"][data["matches"]["is_final"]], ["season", "winner"]),
        "aliases": {"teams": TEAM_ALIASES, "venues": VENUE_RENAMES},
        "winprob": {k: v for k, v in wp.items() if not k.startswith("_")},
        "v1_comparison": cmp,
    }

    teams = []
    bat = data["batter_season"]
    bowl = data["bowler_season"]
    for team, g in ts.groupby("team"):
        b = data["batting_innings"]
        tb = b[b["batting_team"] == team].groupby("batter").agg(runs=("runs", "sum"), balls=("balls", "sum"),
                                                                 innings=("runs", "size")).reset_index()
        tb = tb.nlargest(8, "runs")
        tb["strike_rate"] = tb["runs"] * 100 / tb["balls"]
        bw = data["bowling_innings"]
        tw = bw[bw["bowling_team"] == team].groupby("bowler").agg(
            wickets=("wickets", "sum"), balls=("legal_balls", "sum"), runs=("runs_conceded", "sum")).reset_index()
        tw = tw.nlargest(8, "wickets")
        tw["economy"] = tw["runs"] * 6 / tw["balls"]
        at = data["team_alltime"].set_index("team").loc[team]
        titles = [int(r["season"]) for r in summary["champions"] if r["winner"] == team]
        teams.append({
            "name": team, "short": TEAM_SHORT.get(team, team), "active": team in ACTIVE_TEAMS,
            "titles": titles,
            "alltime": _clean({k: at[k] for k in ("seasons", "played", "won", "lost", "no_result", "win_pct",
                                                 "first_season", "last_season")}),
            "seasons": _records(g.sort_values("season"), ["season", "played", "won", "lost", "no_result",
                                                         "win_pct", "nrr", "run_rate_for", "run_rate_against"]),
            "top_batters": _records(tb, ["batter", "runs", "balls", "innings", "strike_rate"]),
            "top_bowlers": _records(tw, ["bowler", "wickets", "balls", "economy"]),
        })
    teams.sort(key=lambda t: (not t["active"], t["name"]))

    venues = {
        "all": _records(data["venue_summary"], ["venue", "city", "matches", "first_season", "last_season",
                                                "chase_win_pct", "avg_first_innings", "toss_winner_win_pct",
                                                "field_first_pct"]),
        "by_season": venue_by_season(data["matches"]),
    }

    bc = data["batter_career"]
    bat_cols = ["batter", "team", "innings", "runs", "balls", "strike_rate", "average", "sixes", "sr_rank"]
    players = {
        "thresholds": {"season_min_balls": 100, "career_min_balls": 500, "consistency_min_innings": 30,
                       "season_consistency_min_innings": 8, "bowl_season_min_balls": 120,
                       "bowl_career_min_balls": 600},
        "batting": {"all": _records(bc.nlargest(TOP_N, "runs"), bat_cols)},
        "strike_rate": {"all": _records(bc.nsmallest(TOP_N, "sr_rank"), bat_cols)},
        "consistency": {"all": _records(
            bc[bc["innings"] >= 30].nlargest(TOP_N, "pct_25_plus"),
            ["batter", "team", "innings", "runs", "pct_25_plus", "median_score", "cv", "strike_rate"])},
        "bowling": {"all": _records(data["bowler_career"].nlargest(TOP_N, "wickets"),
                                    ["bowler", "team", "balls", "wickets", "economy", "dot_pct", "balls_per_wicket"])},
    }
    bsc = data["batter_season_consistency"]
    for s in seasons:
        bs = bat[bat["season"] == s]
        players["batting"][str(s)] = _records(bs.nsmallest(TOP_N, "runs_rank"), bat_cols)
        players["strike_rate"][str(s)] = _records(bs.nsmallest(TOP_N, "sr_rank"), bat_cols)
        c = bsc[bsc["season"] == s].merge(bs[["batter", "team", "strike_rate"]], on="batter", how="left")
        players["consistency"][str(s)] = _records(
            c.sort_values(["pct_25_plus", "runs"], ascending=False).head(TOP_N),
            ["batter", "team", "innings", "runs", "pct_25_plus", "median_score", "cv", "strike_rate"])
        bo = bowl[bowl["season"] == s]
        players["bowling"][str(s)] = _records(
            bo.sort_values(["wickets", "economy"], ascending=[False, True]).head(TOP_N),
            ["bowler", "team", "balls", "wickets", "economy", "dot_pct", "balls_per_wicket"])

    return [
        _write("summary.json", summary, out_dir),
        _write("teams.json", {"teams": teams, "head_to_head": _clean(data["head_to_head"].to_dict(orient="records"))}, out_dir),
        _write("venues.json", venues, out_dir),
        _write("players.json", players, out_dir),
    ]
