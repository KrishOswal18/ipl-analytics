import numpy as np
import pandas as pd

from ipl.stats import binomial_summary, toss_tests
from ipl.winprob import FEATURES, add_model_features, fit, predict_raw, previous_season_rr, raw_coefficients


def _fake_matches(n=400, seed=0):
    rng = np.random.default_rng(seed)
    seasons = rng.choice([2010, 2015, 2020, 2024], n)
    toss_won = rng.random(n) < 0.5
    return pd.DataFrame({
        "decided": True,
        "toss_winner_won": toss_won.astype(float),
        "toss_decision": rng.choice(["bat", "field"], n),
        "season": seasons,
        "era": pd.Series(seasons).map({2010: "2008-12", 2015: "2013-17", 2020: "2018-22",
                                       2024: "2023-26 (Impact Player)"}),
        "is_playoff": rng.random(n) < 0.05,
        "bat_first_won": (rng.random(n) < 0.5).astype(float),
    })


def test_binomial_fair_coin_not_significant():
    r = binomial_summary(500, 1000)
    assert r["p_value"] > 0.9 and not r["significant"]
    assert r["ci_low"] < 0.5 < r["ci_high"]


def test_binomial_detects_big_effect():
    assert binomial_summary(600, 1000)["significant"]


def test_toss_tests_structure():
    out = toss_tests(_fake_matches())
    assert out["n_decided"] == 400
    assert set(out["by_decision"]) == {"bat", "field"}
    assert len(out["by_era"]) == 4
    assert 0 <= out["era_chi2"]["p_value"] <= 1


def test_previous_season_rr():
    m = previous_season_rr({2008: 8.0, 2009: 7.5, 2010: 8.1})
    assert m == {2008: 8.0, 2009: 8.0, 2010: 7.5, 2011: 8.1}


def test_raw_coefficients_match_sklearn():
    rng = np.random.default_rng(1)
    n = 3000
    df = pd.DataFrame({
        "runs_needed": rng.integers(1, 150, n), "balls_left": rng.integers(1, 120, n),
        "wickets_left": rng.integers(1, 11, n), "prev_rr": rng.uniform(7.5, 10, n)})
    df = add_model_features(df)
    logit = 2 - 0.4 * df["required_rr"] + 0.3 * df["wickets_left"]
    df["chaser_won"] = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    model, scaler = fit(df)
    coefs = raw_coefficients(model, scaler)
    p_sklearn = model.predict_proba(scaler.transform(df[FEATURES]))[:, 1]
    p_raw = predict_raw(coefs, df["runs_needed"], df["balls_left"], df["wickets_left"], df["prev_rr"])
    np.testing.assert_allclose(p_raw, p_sklearn, atol=1e-9)


def test_model_monotonic_in_obvious_directions():
    rng = np.random.default_rng(2)
    n = 5000
    df = pd.DataFrame({
        "runs_needed": rng.integers(1, 150, n), "balls_left": rng.integers(1, 120, n),
        "wickets_left": rng.integers(1, 11, n), "prev_rr": 8.5})
    df = add_model_features(df)
    logit = 2 - 0.5 * df["required_rr"] + 0.4 * df["wickets_left"]
    df["chaser_won"] = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    coefs = raw_coefficients(*fit(df))
    easy, hard = predict_raw(coefs, [30, 90], [60, 60], [8, 8], 8.5)
    assert easy > hard
    more_wkts, fewer_wkts = predict_raw(coefs, [60, 60], [48, 48], [8, 2], 8.5)
    assert more_wkts > fewer_wkts
