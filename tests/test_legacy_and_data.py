import pandas as pd
import pytest

from ipl import DB_PATH
from ipl.legacy import leaky_winrates, prior_winrates
from ipl.normalise import TEAM_ALIASES


def _games():
    return pd.DataFrame({
        "match_id": [1, 2, 3],
        "start_date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
        "team1": ["A", "A", "A"], "team2": ["B", "B", "B"], "winner": ["A", "A", "B"],
    })


def test_prior_winrates_only_use_earlier_matches():
    m = prior_winrates(_games(), "winner", prior_games=0).set_index("match_id")
    assert pd.isna(m.loc[1, "team1_winrate"])  # no history yet (0/0 with no prior)
    assert m.loc[2, "team1_winrate"] == 1.0     # A won match 1
    assert m.loc[3, "team2_winrate"] == 0.0     # B lost both earlier games
    # match 3's own result (B won) must not affect its features
    assert m.loc[3, "team1_winrate"] == 1.0


def test_leaky_winrates_include_the_match_itself():
    m = leaky_winrates(_games(), "winner").set_index("match_id")
    assert m.loc[1, "team1_winrate"] == pytest.approx(2 / 3)  # uses matches 2 and 3 too


needs_db = pytest.mark.skipif(not DB_PATH.exists(), reason="run `python -m ipl build` first")


@needs_db
def test_built_database_is_clean():
    from ipl.queries import query
    names = query("SELECT DISTINCT batting_team AS t FROM deliveries UNION SELECT DISTINCT winner FROM matches")
    assert not set(names["t"].dropna()) & set(TEAM_ALIASES)
    m = query("SELECT COUNT(*) AS n, COUNT(DISTINCT season) AS s, MIN(season) AS lo FROM matches").iloc[0]
    assert m["s"] >= 10 and m["lo"] == 2008
    # every match has exactly one canonical venue
    v = query("SELECT match_id, COUNT(DISTINCT venue) AS k FROM deliveries GROUP BY 1 HAVING k > 1")
    assert v.empty
    # match venue (from info file) agrees with ball by ball venue after cleaning
    bad = query("SELECT COUNT(*) AS n FROM matches m JOIN (SELECT match_id, ANY_VALUE(venue) AS v "
                "FROM deliveries GROUP BY 1) d USING (match_id) WHERE m.venue <> d.v").iloc[0, 0]
    assert bad == 0


@needs_db
def test_first_innings_totals_match_cricsheet_targets():
    from ipl.queries import query
    # Cricsheet gives the target for full length chases, it must equal our total + 1
    bad = query("SELECT COUNT(*) FROM matches WHERE target_overs = 20 AND NOT is_dl "
                "AND target <> first_innings_runs + 1").iloc[0, 0]
    assert bad == 0
