"""Reproduce my first IPL predictor (github.com/KrishOswal18/ipl-match-predictor)
and compare it with a corrected version on the same Cricsheet data.

The v1 model predicted, after the first innings, whether the side batting
first would win. Features: label-encoded team names, first innings score,
wickets, run rate and each team's historical win rate, with a random forest
and a random 80/20 split. Four problems made its accuracy look better than it
was or made the labels wrong:

1. Leakage: each team's win rate was computed on ALL matches, including the
   test matches, so the label leaked into the features.
2. Random split: matches from the same season land in both train and test,
   which is not how the model would be used (predicting future games).
3. Labels: winner was taken as "team 2 if score2 > score1 else team 1", so
   ties and super overs, rain (D/L) results and no-results were mislabelled.
4. Names: Delhi Daredevils / Delhi Capitals and Kings XI Punjab / Punjab Kings
   were separate teams, so their win rates were split in two.

`compare()` runs v1 exactly as written, then fixes one thing at a time.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from .normalise import normalise_team

V1_FEATURES = ["team1_enc", "team2_enc", "score1", "wickets1", "run_rate1",
               "team1_winrate", "team2_winrate"]
TEST_SEASONS = (2025, 2026)


def v1_match_table(deliveries: pd.DataFrame, team_col: str = "batting_team_raw") -> pd.DataFrame:
    """Match table built the way v1 did it, from deliveries only."""
    reg = deliveries[deliveries["innings"] <= 2]
    sc = reg.groupby(["match_id", "innings"]).agg(
        team=(team_col, "first"), runs=("total_runs", "sum"), wkts=("is_wicket", "sum"),
        season=("season", "first")).reset_index()
    i1 = sc[sc["innings"] == 1].rename(columns={"team": "team1", "runs": "score1", "wkts": "wickets1"})
    i2 = sc[sc["innings"] == 2].rename(columns={"team": "team2", "runs": "score2", "wkts": "wickets2"})
    m = i1[["match_id", "season", "team1", "score1", "wickets1"]].merge(
        i2[["match_id", "team2", "score2", "wickets2"]], on="match_id")
    m["v1_winner"] = np.where(m["score2"] > m["score1"], m["team2"], m["team1"])
    m["run_rate1"] = m["score1"] / 20
    return m


def _encode(m: pd.DataFrame) -> pd.DataFrame:
    le = LabelEncoder().fit(pd.concat([m["team1"], m["team2"]]))
    m = m.copy()
    m["team1_enc"] = le.transform(m["team1"])
    m["team2_enc"] = le.transform(m["team2"])
    return m


def leaky_winrates(m: pd.DataFrame, winner_col: str) -> pd.DataFrame:
    """v1: win rate over every match in the file, test matches included."""
    m = m.copy()
    wins = m[winner_col].value_counts()
    games = pd.concat([m["team1"], m["team2"]]).value_counts()
    m["team1_winrate"] = (m["team1"].map(wins) / m["team1"].map(games)).fillna(0.5)
    m["team2_winrate"] = (m["team2"].map(wins) / m["team2"].map(games)).fillna(0.5)
    return m


def prior_winrates(m: pd.DataFrame, winner_col: str, prior_games: int = 5) -> pd.DataFrame:
    """Fixed: win rate from matches played strictly before this one.

    A small prior (5 games at 50%) keeps new franchises from starting at 0% or 100%.
    """
    m = m.sort_values(["start_date", "match_id"]).copy()
    long = pd.concat([
        pd.DataFrame({"match_id": m["match_id"], "slot": 1, "team": m["team1"], "date": m["start_date"]}),
        pd.DataFrame({"match_id": m["match_id"], "slot": 2, "team": m["team2"], "date": m["start_date"]}),
    ]).merge(m[["match_id", winner_col]], on="match_id")
    long = long.sort_values(["date", "match_id"])
    long["win"] = (long["team"] == long[winner_col]).astype(float)
    g = long.groupby("team")["win"]
    long["prev_wins"] = g.cumsum() - long["win"]
    long["prev_games"] = g.cumcount()
    long["wr"] = (long["prev_wins"] + 0.5 * prior_games) / (long["prev_games"] + prior_games)
    for slot in (1, 2):
        s = long[long["slot"] == slot].set_index("match_id")["wr"]
        m[f"team{slot}_winrate"] = m["match_id"].map(s)
    return m


def _rf() -> RandomForestClassifier:
    return RandomForestClassifier(n_estimators=100, random_state=42)


def _random_split_acc(m: pd.DataFrame, label: str, seeds: int = 20) -> dict:
    """v1 used one split (random_state=42). A test set of ~250 matches is noisy,
    so also report the mean and spread over `seeds` different random splits."""
    accs = []
    for seed in range(seeds):
        X_tr, X_te, y_tr, y_te = train_test_split(m[V1_FEATURES], m[label], test_size=0.2,
                                                  random_state=42 + seed)
        accs.append(accuracy_score(y_te, _rf().fit(X_tr, y_tr).predict(X_te)))
    return {"accuracy": float(accs[0]), "accuracy_mean": float(np.mean(accs)),
            "accuracy_sd": float(np.std(accs)), "n_splits": seeds}


def _season_split(m: pd.DataFrame, test_seasons=TEST_SEASONS):
    tr = m[~m["season"].isin(test_seasons)]
    te = m[m["season"].isin(test_seasons)]
    return tr, te


def compare(deliveries: pd.DataFrame, matches: pd.DataFrame) -> dict:
    out: dict = {}
    raw = v1_match_table(deliveries, "batting_team_raw")
    real = matches.set_index("match_id")

    # how wrong the v1 labels are, checked against Cricsheet's result fields
    real_winner = raw["match_id"].map(real["winner"])
    v1_winner = raw["v1_winner"].map(normalise_team)
    out["labels"] = {
        "matches_with_two_innings": int(len(raw)),
        "no_result_counted_as_result": int(real_winner.isna().sum()),
        "wrong_winner": int((real_winner.notna() & (v1_winner != real_winner)).sum()),
        "ties_or_super_overs": int(raw["match_id"].map(real["decided_by_super_over"]).sum()),
        "dl_matches": int(raw["match_id"].map(real["is_dl"]).sum()),
    }

    # 1. v1 exactly, on the seasons it was built on (2008 to 2022)
    v1 = _encode(leaky_winrates(raw[raw["season"] <= 2022], "v1_winner"))
    v1["label"] = (v1["v1_winner"] == v1["team1"]).astype(int)
    out["v1_as_written_2008_2022"] = {"n": int(len(v1)), **_random_split_acc(v1, "label")}

    # 2. v1 method on all seasons 2008 to 2026
    v1a = _encode(leaky_winrates(raw, "v1_winner"))
    v1a["label"] = (v1a["v1_winner"] == v1a["team1"]).astype(int)
    out["v1_as_written_all_seasons"] = {"n": int(len(v1a)), **_random_split_acc(v1a, "label")}

    # corrected base table: real results, normalised names, decided matches only
    fm = matches[matches["decided"] & matches["second_innings_runs"].notna()].copy()
    fm = fm.rename(columns={"bat_first_team": "team1", "chasing_team": "team2",
                            "first_innings_runs": "score1", "first_innings_wickets": "wickets1"})
    fm["run_rate1"] = fm["score1"] / 20
    fm["label"] = (fm["winner"] == fm["team1"]).astype(int)
    fm = _encode(fm)

    # 3. fix labels and names only, still leaky + random split
    lk = leaky_winrates(fm, "winner")
    out["fixed_labels_still_leaky_random_split"] = {"n": int(len(lk)), **_random_split_acc(lk, "label")}

    # 4. remove leakage, still random split
    pr = prior_winrates(fm, "winner")
    out["no_leakage_random_split"] = {"n": int(len(pr)), **_random_split_acc(pr, "label")}

    # 5. fully corrected: prior win rates + season holdout
    tr, te = _season_split(pr)
    rf = _rf().fit(tr[V1_FEATURES], tr["label"])
    out["corrected_season_holdout"] = {
        "n_train": int(len(tr)), "n_test": int(len(te)),
        "accuracy": float(accuracy_score(te["label"], rf.predict(te[V1_FEATURES]))),
    }
    # 6. simpler model on the same honest split: logistic on score and wickets only
    feats = ["score1", "wickets1"]
    lr = LogisticRegression(max_iter=1000).fit(tr[feats], tr["label"])
    out["logistic_score_wickets_season_holdout"] = {
        "accuracy": float(accuracy_score(te["label"], lr.predict(te[feats])))}
    # 7. baseline: always pick the majority class seen in training
    majority = int(tr["label"].mean() >= 0.5)
    out["baseline_majority_season_holdout"] = {
        "predicts": "bat first wins" if majority else "chasing side wins",
        "accuracy": float((te["label"] == majority).mean()),
    }
    out["test_seasons"] = list(TEST_SEASONS)
    return out
