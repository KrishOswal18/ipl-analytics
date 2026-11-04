"""Statistical tests. The main question: does winning the toss help you win?

The toss is a coin flip, so it is a clean natural experiment. If the toss gave
no edge, the toss winner would win about 50% of decided matches. We test that
with an exact two-sided binomial test, then check whether the effect differs
by the decision taken (bat or field) and by era with chi-square tests.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .features import wilson_interval
from .normalise import ERA_ORDER

ALPHA = 0.05


def binomial_summary(k: int, n: int, p0: float = 0.5) -> dict:
    res = stats.binomtest(int(k), int(n), p0, alternative="two-sided")
    lo, hi = wilson_interval(int(k), int(n))
    return {
        "wins": int(k),
        "n": int(n),
        "rate": k / n if n else float("nan"),
        "ci_low": lo,
        "ci_high": hi,
        "p_value": float(res.pvalue),
        "significant": bool(res.pvalue < ALPHA),
    }


def toss_tests(matches: pd.DataFrame) -> dict:
    """All toss related tests on decided matches (super-over results count)."""
    m = matches[matches["decided"]].copy()
    m["toss_winner_won"] = m["toss_winner_won"].astype(bool)

    out: dict = {"n_decided": int(len(m)), "alpha": ALPHA}
    out["overall"] = binomial_summary(m["toss_winner_won"].sum(), len(m))

    out["by_decision"] = {}
    for dec in ("bat", "field"):
        sub = m[m["toss_decision"] == dec]
        out["by_decision"][dec] = binomial_summary(sub["toss_winner_won"].sum(), len(sub))
    table = pd.crosstab(m["toss_decision"], m["toss_winner_won"])
    chi2, p, dof, _ = stats.chi2_contingency(table.to_numpy())
    out["decision_chi2"] = {"chi2": float(chi2), "dof": int(dof), "p_value": float(p),
                            "significant": bool(p < ALPHA)}

    out["by_era"] = {}
    for era in ERA_ORDER:
        sub = m[m["era"] == era]
        row = binomial_summary(sub["toss_winner_won"].sum(), len(sub))
        row["field_first_pct"] = float((sub["toss_decision"] == "field").mean())
        out["by_era"][era] = row
    table = pd.crosstab(m["era"], m["toss_winner_won"]).reindex(ERA_ORDER)
    chi2, p, dof, _ = stats.chi2_contingency(table.to_numpy())
    out["era_chi2"] = {"chi2": float(chi2), "dof": int(dof), "p_value": float(p),
                       "significant": bool(p < ALPHA)}

    # Playoffs vs league stage, captains might treat the toss differently in knockouts
    out["by_stage"] = {}
    for label, sub in (("league", m[~m["is_playoff"]]), ("playoffs", m[m["is_playoff"]])):
        out["by_stage"][label] = binomial_summary(sub["toss_winner_won"].sum(), len(sub))

    # Separate question: does chasing win more often than batting first?
    chase_won = (m["bat_first_won"] == 0)
    out["chasing"] = binomial_summary(chase_won.sum(), len(m))
    out["chasing_by_era"] = {}
    for era in ERA_ORDER:
        sub = m[m["era"] == era]
        out["chasing_by_era"][era] = binomial_summary((sub["bat_first_won"] == 0).sum(), len(sub))

    # Effect size: toss win rate minus 50%, in percentage points
    out["effect_pp"] = (out["overall"]["rate"] - 0.5) * 100
    # Minimum detectable effect: with this n, a true rate of 50% +- ~2.8/sqrt(n)
    # (80% power, two-sided 5%) is about the smallest edge we could reliably see.
    out["mde_pp"] = float(100 * (1.96 + 0.84) * 0.5 / np.sqrt(len(m)))
    return out


def venue_toss_tests(matches: pd.DataFrame, min_matches: int = 40) -> pd.DataFrame:
    """Per ground binomial tests with a Bonferroni correction.

    Many grounds means many tests, so one ground showing p < 0.05 by chance is
    expected. Bonferroni divides alpha by the number of grounds tested.
    """
    m = matches[matches["decided"]]
    rows = []
    for venue, sub in m.groupby("venue"):
        if len(sub) < min_matches:
            continue
        r = binomial_summary(sub["toss_winner_won"].astype(bool).sum(), len(sub))
        r["venue"] = venue
        rows.append(r)
    df = pd.DataFrame(rows).sort_values("rate", ascending=False).reset_index(drop=True)
    df["p_bonferroni"] = np.minimum(df["p_value"] * len(df), 1.0)
    df["significant_after_correction"] = df["p_bonferroni"] < ALPHA
    return df
