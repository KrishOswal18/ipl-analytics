"""Build clean match level and player level tables and store them in DuckDB."""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from . import DB_PATH
from .features import (
    BALLS_PER_INNINGS, BOWLER_WICKETS, NOT_A_DISMISSAL, nrr_balls, phase_of_over,
    run_rate_differential,
)
from .normalise import (
    era_of, normalise_city, normalise_season, normalise_team, normalise_venue,
)


def clean_deliveries(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.copy()
    d["season"] = d["start_date"].dt.year.astype("int64")
    d["season_label"] = raw["season"].astype(str)
    d["batting_team_raw"] = d["batting_team"]
    d["batting_team"] = d["batting_team"].map(normalise_team)
    d["bowling_team"] = d["bowling_team"].map(normalise_team)
    d["venue_raw"] = d["venue"]
    d["venue"] = d["venue"].map(normalise_venue)
    d["is_super_over"] = d["innings"] > 2
    d["over"] = np.floor(d["ball"]).astype("int64")
    d["phase"] = d["over"].map(phase_of_over)
    d["is_legal"] = (d["wides"] == 0) & (d["noballs"] == 0)
    d["faced"] = d["wides"] == 0  # no-balls count as a ball faced by the batter
    d["total_runs"] = d["runs_off_bat"] + d["extras"]
    d["bowler_runs"] = d["runs_off_bat"] + d["wides"] + d["noballs"]
    wt = d["wicket_type"]
    d["is_wicket"] = d["player_dismissed"].notna() & ~wt.isin(NOT_A_DISMISSAL)
    d["is_bowler_wicket"] = wt.isin(BOWLER_WICKETS)
    boundary = d["non_boundary"].isna()
    d["is_four"] = (d["runs_off_bat"] == 4) & boundary
    d["is_six"] = (d["runs_off_bat"] == 6) & boundary
    d["is_dot"] = d["is_legal"] & (d["total_runs"] == 0)
    return d


def build_innings(d: pd.DataFrame, info: pd.DataFrame) -> pd.DataFrame:
    reg = d[~d["is_super_over"]]
    inn = (
        reg.groupby(["match_id", "innings"], as_index=False)
        .agg(batting_team=("batting_team", "first"), bowling_team=("bowling_team", "first"),
             runs=("total_runs", "sum"), wickets=("is_wicket", "sum"),
             legal_balls=("is_legal", "sum"), fours=("is_four", "sum"), sixes=("is_six", "sum"))
    )
    inn = inn.merge(info[["match_id", "target_overs"]], on="match_id", how="left")
    # rain-reduced chases carry their reduced quota in target_overs
    quota = np.where(
        inn["target_overs"].notna() & (inn["target_overs"] < 20),
        np.round(inn["target_overs"].fillna(20) * 6),
        BALLS_PER_INNINGS,
    ).astype("int64")
    # a first innings can be longer than the later reduced quota (rain after it ended)
    inn["quota_balls"] = np.maximum(quota, np.where(inn["innings"] == 1, inn["legal_balls"], 0))
    inn["nrr_balls"] = [nrr_balls(b, w, q) for b, w, q in
                        zip(inn["legal_balls"], inn["wickets"], inn["quota_balls"])]
    return inn.drop(columns="target_overs")


def build_matches(info: pd.DataFrame, innings: pd.DataFrame) -> pd.DataFrame:
    m = info.copy()
    m["season"] = [normalise_season(lbl, dt) for lbl, dt in zip(m["season"], m["start_date"])]
    m["era"] = m["season"].map(era_of)
    for col in ("team_a", "team_b", "toss_winner", "winner", "eliminator"):
        m[col] = m[col].map(normalise_team) if col in m else None
    m["venue_raw"] = m["venue"]
    m["venue"] = m["venue"].map(normalise_venue)
    m["city"] = m["city"].map(normalise_city)
    m["outcome"] = m.get("outcome").fillna("result")
    # ties settled by a super over: the eliminator is the match winner
    m["winner"] = m["winner"].fillna(m["eliminator"])
    m["decided_by_super_over"] = m["eliminator"].notna()
    m["is_dl"] = m.get("method").notna()
    m["is_playoff"] = m["match_number"].isna()

    i1 = innings[innings["innings"] == 1].set_index("match_id")
    i2 = innings[innings["innings"] == 2].set_index("match_id")
    m["bat_first_team"] = m["match_id"].map(i1["batting_team"])
    m["chasing_team"] = m["match_id"].map(i2["batting_team"])
    # abandoned games with only one (or zero) innings: infer from the toss
    toss_bat = np.where(m["toss_decision"] == "bat", m["toss_winner"],
                        np.where(m["toss_winner"] == m["team_a"], m["team_b"], m["team_a"]))
    m["bat_first_team"] = m["bat_first_team"].fillna(pd.Series(toss_bat, index=m.index))
    other = np.where(m["bat_first_team"] == m["team_a"], m["team_b"], m["team_a"])
    m["chasing_team"] = m["chasing_team"].fillna(pd.Series(other, index=m.index))

    for k, src in (("first", i1), ("second", i2)):
        m[f"{k}_innings_runs"] = m["match_id"].map(src["runs"])
        m[f"{k}_innings_wickets"] = m["match_id"].map(src["wickets"])
        m[f"{k}_innings_balls"] = m["match_id"].map(src["legal_balls"])
    m["target"] = m["target_runs"].fillna(m["first_innings_runs"] + 1)

    m["decided"] = m["winner"].notna()
    m["toss_winner_won"] = np.where(m["decided"], m["toss_winner"] == m["winner"], np.nan)
    m["bat_first_won"] = np.where(m["decided"], m["bat_first_team"] == m["winner"], np.nan)
    m["toss_winner_fielded"] = m["toss_decision"] == "field"

    last_date = m.groupby("season")["start_date"].transform("max")
    m["is_final"] = m["is_playoff"] & (m["start_date"] == last_date)
    cols = [
        "match_id", "season", "era", "start_date", "match_number", "is_playoff", "is_final",
        "venue", "venue_raw", "city", "team_a", "team_b", "toss_winner", "toss_decision",
        "toss_winner_fielded", "bat_first_team", "chasing_team", "winner", "outcome",
        "winner_runs", "winner_wickets", "decided", "decided_by_super_over", "is_dl",
        "target", "target_overs", "first_innings_runs", "first_innings_wickets",
        "first_innings_balls", "second_innings_runs", "second_innings_wickets",
        "second_innings_balls", "toss_winner_won", "bat_first_won", "player_of_match",
    ]
    return m[cols].sort_values(["start_date", "match_id"]).reset_index(drop=True)


def build_team_matches(matches: pd.DataFrame, innings: pd.DataFrame) -> pd.DataFrame:
    """Two rows per completed match, one from each side's point of view."""
    i = innings[innings["innings"] <= 2]
    both = i.groupby("match_id").filter(lambda g: len(g) == 2)
    rows = both.merge(both, on="match_id", suffixes=("", "_opp"))
    rows = rows[rows["innings"] != rows["innings_opp"]]
    tm = pd.DataFrame({
        "match_id": rows["match_id"].to_numpy(),
        "team": rows["batting_team"].to_numpy(),
        "opponent": rows["batting_team_opp"].to_numpy(),
        "batted_first": (rows["innings"] == 1).to_numpy(),
        "runs_for": rows["runs"].to_numpy(),
        "balls_for": rows["legal_balls"].to_numpy(),
        "nrr_balls_for": rows["nrr_balls"].to_numpy(),
        "runs_against": rows["runs_opp"].to_numpy(),
        "balls_against": rows["legal_balls_opp"].to_numpy(),
        "nrr_balls_against": rows["nrr_balls_opp"].to_numpy(),
    })
    meta = matches[["match_id", "season", "era", "venue", "winner", "outcome", "decided",
                    "toss_winner", "is_playoff"]]
    tm = tm.merge(meta, on="match_id", how="left")
    tm["won"] = tm["decided"] & (tm["team"] == tm["winner"])
    tm["won_toss"] = tm["team"] == tm["toss_winner"]
    tm["run_rate_diff"] = run_rate_differential(
        tm["runs_for"], tm["nrr_balls_for"], tm["runs_against"], tm["nrr_balls_against"])
    return tm.drop(columns=["winner", "toss_winner"])


def build_batting(d: pd.DataFrame) -> pd.DataFrame:
    reg = d[~d["is_super_over"]]
    keys = ["match_id", "season", "innings", "batting_team"]
    bat = (reg.groupby(keys + ["striker"], as_index=False)
           .agg(runs=("runs_off_bat", "sum"), balls=("faced", "sum"),
                fours=("is_four", "sum"), sixes=("is_six", "sum"))
           .rename(columns={"striker": "batter"}))
    outs = reg[reg["is_wicket"]]
    outs = outs.groupby(keys + ["player_dismissed"]).size().rename("dismissed").reset_index()
    outs = outs.rename(columns={"player_dismissed": "batter"})
    bat = bat.merge(outs, on=keys + ["batter"], how="outer")
    bat[["runs", "balls", "fours", "sixes"]] = bat[["runs", "balls", "fours", "sixes"]].fillna(0).astype("int64")
    bat["out"] = bat["dismissed"].fillna(0).astype("int64") > 0
    return bat.drop(columns="dismissed")


def build_bowling(d: pd.DataFrame) -> pd.DataFrame:
    reg = d[~d["is_super_over"]]
    return (reg.groupby(["match_id", "season", "innings", "bowling_team", "bowler"], as_index=False)
            .agg(legal_balls=("is_legal", "sum"), runs_conceded=("bowler_runs", "sum"),
                 wickets=("is_bowler_wicket", "sum"), dots=("is_dot", "sum")))


def build_all(info_raw: pd.DataFrame, deliveries_raw: pd.DataFrame) -> dict[str, pd.DataFrame]:
    d = clean_deliveries(deliveries_raw)
    innings = build_innings(d, info_raw)
    matches = build_matches(info_raw, innings)
    return {
        "deliveries": d,
        "innings": innings,
        "matches": matches,
        "team_matches": build_team_matches(matches, innings),
        "batting_innings": build_batting(d),
        "bowling_innings": build_bowling(d),
    }


def write_duckdb(tables: dict[str, pd.DataFrame], db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    con = duckdb.connect(str(db_path))
    try:
        for name, df in tables.items():
            con.register("tmp_df", df)
            con.execute(f"CREATE TABLE {name} AS SELECT * FROM tmp_df")
            con.unregister("tmp_df")
    finally:
        con.close()
