"""Second innings win probability model.

Every legal ball of every clean chase becomes one training row describing the
state after that ball (runs needed, balls left, wickets left) and the label
is whether the chasing side went on to win. A logistic regression on a few
hand made features is enough to beat the baselines and is small enough to
run in the browser: the dashboard calculator uses the exported coefficients.

Evaluation is by season, not by random split. Balls from the same match are
highly correlated, so a random split would leak. 2025 and 2026 are the test
seasons and are only touched once, at the end.

Scoring has gone up a lot (average first innings 161 in 2008, 193 in 2026), so
a chase of 10 an over meant something different in 2010. The training window
(which first season to start from) is therefore picked on a validation season
(2024, with training data ending 2023) before the test seasons are scored.

The model also gets the previous season's overall run rate ("prev_rr") as a
measure of the scoring environment. It is known before a season starts, so it
does not leak anything from the match being predicted. Without it the model
was well calibrated on its training seasons but badly underrated chasers in
2025 and 2026, because a required rate of 10 is simply easier now.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss
from sklearn.preprocessing import StandardScaler

from .features import BALLS_PER_INNINGS, required_run_rate

FEATURES = ["runs_needed", "balls_left", "wickets_left", "required_rr", "wkts_x_balls", "rn_per_wkt",
            "prev_rr"]
TEST_SEASONS = (2025, 2026)
VALIDATION_SEASON = 2024
WINDOW_STARTS = (2008, 2013, 2018, 2021, 2023)


def add_model_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["required_rr"] = required_run_rate(df["runs_needed"], df["balls_left"])
    # wickets matter more when lots of balls are left (and vice versa)
    df["wkts_x_balls"] = df["wickets_left"] * df["balls_left"] / BALLS_PER_INNINGS
    # runs needed per wicket in hand, a rough "resources" ratio
    df["rn_per_wkt"] = df["runs_needed"] / np.maximum(df["wickets_left"], 1)
    return df


def previous_season_rr(season_rr: dict[int, float]) -> dict[int, float]:
    """Map each season to the run rate of the season before it.

    The first season has no previous one, so it uses its own value (only
    relevant if the training window starts in 2008).
    """
    seasons = sorted(season_rr)
    out = {seasons[0]: season_rr[seasons[0]]}
    for prev, cur in zip(seasons, seasons[1:]):
        out[cur] = season_rr[prev]
    out[seasons[-1] + 1] = season_rr[seasons[-1]]  # for predicting the next season
    return out


def chase_states(deliveries: pd.DataFrame, matches: pd.DataFrame,
                 season_rr: dict[int, float]) -> pd.DataFrame:
    """One row per legal ball of each full-length, decided, non-D/L chase."""
    ok = matches[
        matches["decided"] & ~matches["is_dl"] & ~matches["decided_by_super_over"]
        & (matches["target_overs"].fillna(20) == 20) & matches["second_innings_runs"].notna()
    ][["match_id", "season", "target", "chasing_team", "winner"]]
    d = deliveries[(deliveries["innings"] == 2)].merge(ok, on="match_id", suffixes=("", "_m"))
    d = d.sort_values(["match_id", "ball", "actual_delivery"] if "actual_delivery" in d else ["match_id", "ball"])
    g = d.groupby("match_id")
    d["runs_so_far"] = g["total_runs"].cumsum()
    d["wkts_so_far"] = g["is_wicket"].cumsum()
    d["balls_so_far"] = g["is_legal"].cumsum()
    d = d[d["is_legal"]]
    st = pd.DataFrame({
        "match_id": d["match_id"].to_numpy(),
        "season": d["season_m"].to_numpy() if "season_m" in d else d["season"].to_numpy(),
        "runs_needed": (d["target"] - d["runs_so_far"]).to_numpy(),
        "balls_left": (BALLS_PER_INNINGS - d["balls_so_far"]).to_numpy(),
        "wickets_left": (10 - d["wkts_so_far"]).to_numpy(),
        "chaser_won": (d["chasing_team"] == d["winner"]).astype(int).to_numpy(),
    })
    # once the target is reached or the side is all out the result is known, drop it
    st = st[(st["runs_needed"] > 0) & (st["wickets_left"] > 0) & (st["balls_left"] > 0)].copy()
    st["prev_rr"] = st["season"].map(previous_season_rr(season_rr))
    return add_model_features(st).reset_index(drop=True)


def fit(train: pd.DataFrame) -> tuple[LogisticRegression, StandardScaler]:
    scaler = StandardScaler().fit(train[FEATURES])
    model = LogisticRegression(max_iter=2000, C=1.0)
    model.fit(scaler.transform(train[FEATURES]), train["chaser_won"])
    return model, scaler


def raw_coefficients(model: LogisticRegression, scaler: StandardScaler) -> dict:
    """Fold the scaler into the weights so p = sigmoid(b + sum(w_i * x_i)) on raw inputs."""
    w = model.coef_[0] / scaler.scale_
    b = model.intercept_[0] - float(np.sum(model.coef_[0] * scaler.mean_ / scaler.scale_))
    return {"intercept": float(b), "weights": {f: float(v) for f, v in zip(FEATURES, w)}}


def predict_raw(coefs: dict, runs_needed, balls_left, wickets_left, prev_rr) -> np.ndarray:
    """Same formula the dashboard uses, so tests can check Python and JS agree."""
    n = len(np.atleast_1d(runs_needed))
    df = add_model_features(pd.DataFrame({
        "runs_needed": np.atleast_1d(runs_needed), "balls_left": np.atleast_1d(balls_left),
        "wickets_left": np.atleast_1d(wickets_left), "prev_rr": np.broadcast_to(prev_rr, n)}))
    z = coefs["intercept"] + sum(coefs["weights"][f] * df[f].to_numpy() for f in FEATURES)
    return 1.0 / (1.0 + np.exp(-z))


def _scores(y, p) -> dict:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return {"accuracy": float(accuracy_score(y, p >= 0.5)), "log_loss": float(log_loss(y, p, labels=[0, 1])),
            "brier": float(brier_score_loss(y, p))}


def select_window(states: pd.DataFrame, val_season: int = VALIDATION_SEASON,
                  starts=WINDOW_STARTS) -> tuple[int, list[dict]]:
    """Pick the first training season by log-loss on the validation season."""
    val = states[states["season"] == val_season]
    rows = []
    for start in starts:
        tr = states[(states["season"] >= start) & (states["season"] < val_season)]
        model, scaler = fit(tr)
        p = model.predict_proba(scaler.transform(val[FEATURES]))[:, 1]
        rows.append({"start": int(start), **_scores(val["chaser_won"].to_numpy(), p)})
    best = min(rows, key=lambda r: r["log_loss"])["start"]
    return best, rows


def evaluate(states: pd.DataFrame, test_seasons=TEST_SEASONS) -> dict:
    start, window_rows = select_window(states)
    test = states[states["season"].isin(test_seasons)]
    pre_test = states[states["season"] < min(test_seasons)]
    train = pre_test[pre_test["season"] >= start]
    model, scaler = fit(train)
    # same model on every season before the test, to show what the window choice is worth
    all_model, all_scaler = fit(pre_test)
    p_all = all_model.predict_proba(all_scaler.transform(test[FEATURES]))[:, 1]
    p_model = model.predict_proba(scaler.transform(test[FEATURES]))[:, 1]

    # Baseline 1: always predict the training chase win rate
    base_rate = float(train["chaser_won"].mean())
    p_const = np.full(len(test), base_rate)
    # Baseline 2: a logistic regression on required run rate only
    rr_model = LogisticRegression(max_iter=1000).fit(train[["required_rr"]], train["chaser_won"])
    p_rr = rr_model.predict_proba(test[["required_rr"]])[:, 1]

    y = test["chaser_won"].to_numpy()
    res = {
        "train_seasons": [int(train["season"].min()), int(train["season"].max())],
        "test_seasons": [int(s) for s in test_seasons],
        "n_train_states": int(len(train)), "n_test_states": int(len(test)),
        "n_train_matches": int(train["match_id"].nunique()),
        "n_test_matches": int(test["match_id"].nunique()),
        "train_chase_win_rate": base_rate,
        "window_selection": {"validation_season": VALIDATION_SEASON, "chosen_start": int(start),
                             "candidates": window_rows},
        "model": _scores(y, p_model),
        "model_all_seasons": _scores(y, p_all),
        "baseline_constant": _scores(y, p_const),
        "baseline_required_rr": _scores(y, p_rr),
        "coefficients": raw_coefficients(model, scaler),
    }
    # how the model does per test season
    res["by_season"] = {}
    for s in test_seasons:
        mask = test["season"].to_numpy() == s
        res["by_season"][str(s)] = _scores(y[mask], p_model[mask])
    # accuracy at fixed points of the chase (start of over 6, 11, 16)
    res["by_checkpoint"] = {}
    for balls_left in (84, 54, 24):
        mask = test["balls_left"].to_numpy() == balls_left
        if mask.sum():
            res["by_checkpoint"][str(balls_left)] = {
                **_scores(y[mask], p_model[mask]), "n": int(mask.sum()),
                "baseline_constant_accuracy": float(accuracy_score(y[mask], p_const[mask] >= 0.5)),
            }
    # calibration: predicted vs observed in 10 bins
    bins = np.clip((p_model * 10).astype(int), 0, 9)
    cal = (pd.DataFrame({"bin": bins, "p": p_model, "y": y}).groupby("bin")
           .agg(predicted=("p", "mean"), observed=("y", "mean"), n=("y", "size")).reset_index())
    res["calibration"] = cal.to_dict(orient="records")
    p_tr = model.predict_proba(scaler.transform(train[FEATURES]))[:, 1]
    bins_tr = np.clip((p_tr * 10).astype(int), 0, 9)
    cal_tr = (pd.DataFrame({"bin": bins_tr, "p": p_tr, "y": train["chaser_won"].to_numpy()}).groupby("bin")
              .agg(predicted=("p", "mean"), observed=("y", "mean"), n=("y", "size")).reset_index())
    res["calibration_train"] = cal_tr.to_dict(orient="records")
    # same check for the model without the scoring environment features
    base_feats = [f for f in FEATURES if f != "prev_rr"]
    sc_nb = StandardScaler().fit(train[base_feats])
    m_nb = LogisticRegression(max_iter=2000).fit(sc_nb.transform(train[base_feats]), train["chaser_won"])
    p_nb = m_nb.predict_proba(sc_nb.transform(test[base_feats]))[:, 1]
    res["model_without_scoring_level"] = _scores(y, p_nb)
    bins_nb = np.clip((p_nb * 10).astype(int), 0, 9)
    res["calibration_without_scoring_level"] = (
        pd.DataFrame({"bin": bins_nb, "p": p_nb, "y": y}).groupby("bin")
        .agg(predicted=("p", "mean"), observed=("y", "mean"), n=("y", "size")).reset_index()
        .to_dict(orient="records"))
    res["latest_prev_rr"] = float(test.loc[test["season"] == max(test_seasons), "prev_rr"].iloc[0])
    res["_test_frame"] = test.assign(p_model=p_model)
    return res
