import pytest

from ipl.normalise import (
    era_of, normalise_city, normalise_season, normalise_team, normalise_venue, team_short,
)


@pytest.mark.parametrize("raw,clean", [
    ("Delhi Daredevils", "Delhi Capitals"),
    ("Kings XI Punjab", "Punjab Kings"),
    ("Royal Challengers Bangalore", "Royal Challengers Bengaluru"),
    ("Rising Pune Supergiants", "Rising Pune Supergiant"),
    ("Mumbai Indians", "Mumbai Indians"),
    ("  Delhi   Daredevils ", "Delhi Capitals"),
])
def test_team_aliases(raw, clean):
    assert normalise_team(raw) == clean


def test_different_franchises_stay_separate():
    # same city, different owners: these must NOT be merged
    assert normalise_team("Deccan Chargers") != normalise_team("Sunrisers Hyderabad")
    assert normalise_team("Gujarat Lions") != normalise_team("Gujarat Titans")


def test_team_missing_values():
    assert normalise_team(None) is None
    assert normalise_team(float("nan")) is None


def test_team_short_codes_follow_aliases():
    assert team_short("Kings XI Punjab") == "PBKS"
    assert team_short("Delhi Daredevils") == "DC"


@pytest.mark.parametrize("raw,clean", [
    ("Wankhede Stadium, Mumbai", "Wankhede Stadium"),
    ("Wankhede Stadium", "Wankhede Stadium"),
    ("M.Chinnaswamy Stadium", "M Chinnaswamy Stadium"),
    ("M Chinnaswamy Stadium, Bangalore", "M Chinnaswamy Stadium"),
    ("M Chinnaswamy Stadium, Bengaluru", "M Chinnaswamy Stadium"),
    ("MA Chidambaram Stadium, Chepauk, Chennai", "MA Chidambaram Stadium"),
    ("Feroz Shah Kotla", "Arun Jaitley Stadium"),
    ("Arun Jaitley Stadium, Delhi", "Arun Jaitley Stadium"),
    ("Sardar Patel Stadium, Motera", "Narendra Modi Stadium"),
    ("Punjab Cricket Association Stadium, Mohali", "Punjab Cricket Association IS Bindra Stadium"),
    ("Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh",
     "Punjab Cricket Association IS Bindra Stadium"),
    ("Sheikh Zayed Stadium", "Zayed Cricket Stadium"),
    ("Zayed Cricket Stadium, Abu Dhabi", "Zayed Cricket Stadium"),
    ("Subrata Roy Sahara Stadium", "Maharashtra Cricket Association Stadium"),
    ("Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium, Visakhapatnam", "ACA-VDCA Cricket Stadium"),
    ("Maharaja Yadavindra Singh International Cricket Stadium, Mullanpur",
     "Maharaja Yadavindra Singh International Cricket Stadium"),
    ("Maharaja Yadavindra Singh International Cricket Stadium, New Chandigarh",
     "Maharaja Yadavindra Singh International Cricket Stadium"),
    ("Rajiv Gandhi International Stadium, Uppal, Hyderabad", "Rajiv Gandhi International Stadium"),
    ("New Wanderers Stadium", "Wanderers Stadium"),
    ("Wanderers Stadium, Johannesburg", "Wanderers Stadium"),
])
def test_venue_variants(raw, clean):
    assert normalise_venue(raw) == clean


def test_venue_keeps_unknown_names():
    assert normalise_venue("Some New Ground") == "Some New Ground"


def test_venue_is_idempotent():
    for v in ["Feroz Shah Kotla", "Wankhede Stadium, Mumbai", "Sardar Patel Stadium, Motera"]:
        once = normalise_venue(v)
        assert normalise_venue(once) == once


@pytest.mark.parametrize("label,date,season", [
    ("2007/08", "2008-04-18", 2008),
    ("2009/10", "2010-03-12", 2010),
    ("2020/21", "2020-09-19", 2020),
    ("2023", "2023-03-31", 2023),
    ("2007/08", None, 2008),
    ("2020/21", None, 2020),
    ("2019", None, 2019),
])
def test_season(label, date, season):
    assert normalise_season(label, date) == season


def test_season_bad_label():
    with pytest.raises(ValueError):
        normalise_season("next year")


def test_eras():
    assert era_of(2008) == "2008-12"
    assert era_of(2017) == "2013-17"
    assert era_of(2022) == "2018-22"
    assert era_of(2023).startswith("2023")


def test_city():
    assert normalise_city("Bangalore") == "Bengaluru"
    assert normalise_city(None) is None
