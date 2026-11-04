import math

import numpy as np
import pandas as pd
import pytest

from ipl.features import (
    batting_average, chase_state, consistency_metrics, net_run_rate, nrr_balls, phase_of_over,
    rank_within, required_run_rate, run_rate, run_rate_differential, strike_rate, wilson_interval,
)


def test_phase_boundaries():
    assert phase_of_over(0) == "powerplay"
    assert phase_of_over(5) == "powerplay"
    assert phase_of_over(6) == "middle"
    assert phase_of_over(14) == "middle"
    assert phase_of_over(15) == "death"
    assert phase_of_over(19) == "death"


def test_run_rate_and_strike_rate():
    assert run_rate(180, 120) == pytest.approx(9.0)
    assert strike_rate(50, 25) == pytest.approx(200.0)
    assert math.isnan(run_rate(10, 0))
    assert math.isnan(strike_rate(0, 0))
    np.testing.assert_allclose(strike_rate([10, 30], [10, 20]), [100.0, 150.0])


def test_nrr_balls_all_out_uses_full_quota():
    assert nrr_balls(100, 10) == 120  # bowled out in 16.4 overs counts as 20 overs
    assert nrr_balls(100, 7) == 100
    assert nrr_balls(60, 10, quota_balls=90) == 90


def test_run_rate_differential():
    # 180 off 20 overs vs 150 off 20 overs = 9.0 - 7.5
    assert run_rate_differential(180, 120, 150, 120) == pytest.approx(1.5)


def test_net_run_rate_is_aggregate_not_mean():
    tm = pd.DataFrame({"runs_for": [200, 100], "nrr_balls_for": [120, 60],
                       "runs_against": [150, 120], "nrr_balls_against": [120, 120]})
    # (300 / 30 overs) - (270 / 40 overs) = 10 - 6.75
    assert net_run_rate(tm) == pytest.approx(3.25)


def test_batting_average():
    assert batting_average(300, 10) == 30
    assert math.isnan(batting_average(50, 0))


def test_consistency_metrics():
    m = consistency_metrics([30, 30, 30, 30])
    assert m["cv"] == 0
    assert m["pct_threshold"] == 1.0
    m2 = consistency_metrics([0, 0, 100, 0])
    assert m2["median"] == 0
    assert m2["pct_threshold"] == 0.25
    assert m2["cv"] > 1
    assert consistency_metrics([])["innings"] == 0


def test_rank_within_groups_and_ties():
    df = pd.DataFrame({"season": [1, 1, 1, 2, 2], "sr": [150, 120, 150, 110, 130]})
    assert rank_within(df, "sr", "season").tolist() == [1, 3, 1, 2, 1]
    assert rank_within(df, "sr", ascending=True).tolist() == [4, 2, 4, 1, 3]


def test_required_run_rate_caps():
    assert required_run_rate(60, 60) == pytest.approx(6.0)
    assert required_run_rate(30, 0) == 36.0
    assert required_run_rate(-5, 30) == 0.0


def test_chase_state():
    s = chase_state(target=181, runs_so_far=100, legal_balls_so_far=72, wickets_so_far=3)
    assert s == {"runs_needed": 81, "balls_left": 48, "wickets_left": 7,
                 "required_rr": pytest.approx(10.125)}


def test_wilson_interval_contains_rate():
    lo, hi = wilson_interval(634, 1234)
    assert lo < 634 / 1234 < hi
    assert 0.48 < lo < 0.49 and 0.54 < hi < 0.55
