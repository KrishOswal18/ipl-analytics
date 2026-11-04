"""Feature functions. Kept pure (inputs in, numbers out) so they are easy to test."""

from __future__ import annotations

import numpy as np
import pandas as pd

BALLS_PER_INNINGS = 120
BOWLER_WICKETS = {"bowled", "caught", "caught and bowled", "lbw", "stumped", "hit wicket"}
NOT_A_DISMISSAL = {"retired hurt"}


def phase_of_over(over: int) -> str:
    """Over index is 0 based as in Cricsheet: 0-5 powerplay, 6-14 middle, 15+ death."""
    if over < 6:
        return "powerplay"
    if over < 15:
        return "middle"
    return "death"


def run_rate(runs, balls):
    """Runs per six legal balls. Returns NaN when no balls were bowled."""
    runs = np.asarray(runs, dtype=float)
    balls = np.asarray(balls, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(balls > 0, runs * 6.0 / balls, np.nan)
    return out if out.ndim else float(out)


def strike_rate(runs, balls):
    """Batting strike rate: runs per 100 balls faced."""
    runs = np.asarray(runs, dtype=float)
    balls = np.asarray(balls, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(balls > 0, runs * 100.0 / balls, np.nan)
    return out if out.ndim else float(out)


def nrr_balls(legal_balls: int, wickets: int, quota_balls: int = BALLS_PER_INNINGS) -> int:
    """Balls used for net run rate.

    IPL rules: a side that is bowled out is treated as if it faced its full
    quota of overs, otherwise the balls actually faced count.
    """
    return quota_balls if wickets >= 10 else legal_balls


def run_rate_differential(runs_for, balls_for, runs_against, balls_against):
    """Scoring rate minus conceding rate, the per match building block of NRR."""
    return run_rate(runs_for, balls_for) - run_rate(runs_against, balls_against)


def net_run_rate(team_matches: pd.DataFrame) -> float:
    """Season style NRR from a team's matches: total runs/overs for minus against."""
    rf = team_matches["runs_for"].sum()
    bf = team_matches["nrr_balls_for"].sum()
    ra = team_matches["runs_against"].sum()
    ba = team_matches["nrr_balls_against"].sum()
    return float(run_rate(rf, bf) - run_rate(ra, ba))


def batting_average(runs: float, dismissals: int) -> float:
    return float(runs) / dismissals if dismissals > 0 else float("nan")


def consistency_metrics(scores, threshold: int = 25) -> dict:
    """Describe how steady a batter's innings-by-innings scores are.

    * cv: coefficient of variation of runs per innings (std / mean), lower is steadier
    * pct_threshold: share of innings with at least `threshold` runs
    * median: median score, less skewed by one big hundred than the mean
    """
    s = np.asarray(list(scores), dtype=float)
    if s.size == 0:
        return {"innings": 0, "mean": np.nan, "median": np.nan, "cv": np.nan, "pct_threshold": np.nan}
    mean = s.mean()
    std = s.std(ddof=1) if s.size > 1 else 0.0
    return {
        "innings": int(s.size),
        "mean": float(mean),
        "median": float(np.median(s)),
        "cv": float(std / mean) if mean > 0 else np.nan,
        "pct_threshold": float((s >= threshold).mean()),
    }


def rank_within(df: pd.DataFrame, value: str, by: str | list[str] | None = None,
                ascending: bool = False) -> pd.Series:
    """Rank `value` (ties share the best rank), optionally inside groups."""
    if by is None:
        return df[value].rank(method="min", ascending=ascending).astype("int64")
    return df.groupby(by)[value].rank(method="min", ascending=ascending).astype("int64")


def chase_state(target: int, runs_so_far: int, legal_balls_so_far: int, wickets_so_far: int,
                quota_balls: int = BALLS_PER_INNINGS) -> dict:
    """State of a chase after some balls: what the win probability model sees."""
    runs_needed = target - runs_so_far
    balls_left = quota_balls - legal_balls_so_far
    wickets_left = 10 - wickets_so_far
    return {
        "runs_needed": runs_needed,
        "balls_left": balls_left,
        "wickets_left": wickets_left,
        "required_rr": required_run_rate(runs_needed, balls_left),
    }


def required_run_rate(runs_needed, balls_left, cap: float = 36.0):
    """Runs per over still needed, capped so the last ball does not explode to infinity."""
    rn = np.asarray(runs_needed, dtype=float)
    bl = np.asarray(balls_left, dtype=float)
    out = np.clip(rn * 6.0 / np.maximum(bl, 1.0), 0.0, cap)
    return out if out.ndim else float(out)


def is_bowler_wicket(wicket_type) -> bool:
    return isinstance(wicket_type, str) and wicket_type in BOWLER_WICKETS


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a proportion k/n."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (float(centre - half), float(centre + half))
