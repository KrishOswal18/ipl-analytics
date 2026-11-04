"""Build the tables from a tiny hand made match so every number can be checked by hand."""

import pandas as pd

from ipl.tables import build_all


def _raw():
    rows = []
    # innings 1: Delhi Daredevils, 2 overs: 6 legal balls each, one wide, one wicket
    balls = [(0.1, 4, 0, None), (0.2, 0, 1, None), (0.2, 1, 0, None), (0.3, 6, 0, None),
             (0.4, 0, 0, "bowled"), (0.5, 1, 0, None), (0.6, 2, 0, None)]
    for b, r, w, wk in balls:
        rows.append(dict(match_id=1, season="2007/08", start_date="2008-04-20",
                         venue="Feroz Shah Kotla", innings=1, ball=b, batting_team="Delhi Daredevils",
                         bowling_team="Kings XI Punjab", striker="A" if b < 0.5 else "B",
                         non_striker="C", bowler="X", runs_off_bat=r, extras=w, wides=w, noballs=0,
                         byes=0, legbyes=0, penalty=0, non_boundary=None, wicket_type=wk,
                         player_dismissed="A" if wk else None, actual_delivery=b))
    # innings 2: Kings XI Punjab chase 15 off 6 balls and win
    for i, r in enumerate([6, 6, 1, 2]):
        rows.append(dict(match_id=1, season="2007/08", start_date="2008-04-20",
                         venue="Feroz Shah Kotla, Delhi", innings=2, ball=0.1 * (i + 1),
                         batting_team="Kings XI Punjab", bowling_team="Delhi Daredevils",
                         striker="P", non_striker="Q", bowler="Y", runs_off_bat=r, extras=0, wides=0,
                         noballs=0, byes=0, legbyes=0, penalty=0, non_boundary=None, wicket_type=None,
                         player_dismissed=None, actual_delivery=0.1 * (i + 1)))
    d = pd.DataFrame(rows)
    d["start_date"] = pd.to_datetime(d["start_date"])
    info = pd.DataFrame([{
        "match_id": 1, "season": "2007/08", "start_date": pd.Timestamp("2008-04-20"),
        "venue": "Feroz Shah Kotla", "city": "Delhi", "team_a": "Delhi Daredevils",
        "team_b": "Kings XI Punjab", "toss_winner": "Kings XI Punjab", "toss_decision": "field",
        "winner": "Kings XI Punjab", "winner_runs": None, "winner_wickets": 10, "outcome": None,
        "eliminator": None, "method": None, "player_of_match": "P", "match_number": 1,
        "target_overs": 20.0, "target_runs": 15}])
    return info, d


def test_tables_by_hand():
    info, d = _raw()
    t = build_all(info, d)
    m = t["matches"].iloc[0]
    assert m["season"] == 2008
    assert m["venue"] == "Arun Jaitley Stadium"
    assert m["bat_first_team"] == "Delhi Capitals"
    assert m["winner"] == "Punjab Kings"
    assert m["first_innings_runs"] == 15   # 14 off the bat + 1 wide
    assert m["first_innings_wickets"] == 1
    assert m["first_innings_balls"] == 6
    assert m["toss_winner_won"] == 1 and m["bat_first_won"] == 0

    bat = t["batting_innings"].set_index("batter")
    assert bat.loc["A", "runs"] == 11 and bat.loc["A", "balls"] == 4 and bool(bat.loc["A", "out"])
    assert bat.loc["A", "fours"] == 1 and bat.loc["A", "sixes"] == 1

    bowl = t["bowling_innings"].set_index("bowler")
    assert bowl.loc["X", "legal_balls"] == 6
    assert bowl.loc["X", "runs_conceded"] == 15
    assert bowl.loc["X", "wickets"] == 1

    tm = t["team_matches"].set_index("team")
    # Punjab: 15 off 4 balls = 22.5 rpo, Delhi: 15 off 6 balls = 15 rpo
    assert tm.loc["Punjab Kings", "run_rate_diff"] == 22.5 - 15.0
    assert bool(tm.loc["Punjab Kings", "won"])
