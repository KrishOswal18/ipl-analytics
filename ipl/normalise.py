"""Cleaning rules that make 19 seasons of IPL data line up.

Three things change across seasons in the raw Cricsheet files:

1. Franchise names. The same franchise shows up under its old and new name
   (Delhi Daredevils became Delhi Capitals in 2019, Kings XI Punjab became
   Punjab Kings in 2021, Royal Challengers Bangalore became Royal Challengers
   Bengaluru in 2024). Defunct sides that were genuinely different franchises
   (Deccan Chargers vs Sunrisers Hyderabad, Gujarat Lions vs Gujarat Titans)
   are kept separate on purpose.
2. Venue names. Cricsheet started adding the city to venue names around 2020,
   some grounds were renamed (Feroz Shah Kotla is now Arun Jaitley Stadium,
   Sardar Patel Stadium in Motera is now Narendra Modi Stadium) and spelling
   varies ("M.Chinnaswamy" vs "M Chinnaswamy").
3. Season labels. Cricsheet labels some seasons by cricket season
   ("2007/08", "2009/10", "2020/21") but every IPL season sits inside one
   calendar year, so the match date's year is the reliable season key.
"""

from __future__ import annotations

import re
from datetime import date, datetime

# old name -> current name of the same franchise
TEAM_ALIASES: dict[str, str] = {
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Rising Pune Supergiants": "Rising Pune Supergiant",
}

TEAM_SHORT: dict[str, str] = {
    "Chennai Super Kings": "CSK",
    "Delhi Capitals": "DC",
    "Deccan Chargers": "DCH",
    "Gujarat Lions": "GL",
    "Gujarat Titans": "GT",
    "Kochi Tuskers Kerala": "KTK",
    "Kolkata Knight Riders": "KKR",
    "Lucknow Super Giants": "LSG",
    "Mumbai Indians": "MI",
    "Pune Warriors": "PWI",
    "Punjab Kings": "PBKS",
    "Rajasthan Royals": "RR",
    "Rising Pune Supergiant": "RPS",
    "Royal Challengers Bengaluru": "RCB",
    "Sunrisers Hyderabad": "SRH",
}

# Franchises that played in the current era (still active in 2022 onwards)
ACTIVE_TEAMS = {
    "Chennai Super Kings", "Delhi Capitals", "Gujarat Titans", "Kolkata Knight Riders",
    "Lucknow Super Giants", "Mumbai Indians", "Punjab Kings", "Rajasthan Royals",
    "Royal Challengers Bengaluru", "Sunrisers Hyderabad",
}

# Trailing ", <place>" parts that Cricsheet appends inconsistently.
# Localities (Chepauk, Uppal, Motera) are stripped too so that
# "MA Chidambaram Stadium, Chepauk" and "MA Chidambaram Stadium" match.
PLACE_SUFFIXES = {
    "Abu Dhabi", "Ahmedabad", "Bengaluru", "Chandigarh", "Chennai", "Chepauk",
    "Delhi", "Dharamsala", "Guwahati", "Hyderabad", "Jaipur", "Kolkata",
    "Lucknow", "Mohali", "Motera", "Mullanpur", "Mumbai", "New Chandigarh",
    "Pune", "Raipur", "Uppal", "Visakhapatnam", "Jamtha", "Nagpur", "Bangalore",
    "Cuttack", "Navi Mumbai", "Kanpur", "Indore", "Ranchi", "Kochi", "Rajkot",
    "Durban", "East London", "Kimberley", "Bloemfontein", "Cape Town",
    "Port Elizabeth", "Centurion", "Johannesburg",
}

# after suffix stripping: old ground name -> current ground name
VENUE_RENAMES: dict[str, str] = {
    "Feroz Shah Kotla": "Arun Jaitley Stadium",
    "Sardar Patel Stadium": "Narendra Modi Stadium",
    "Punjab Cricket Association Stadium": "Punjab Cricket Association IS Bindra Stadium",
    "Sheikh Zayed Stadium": "Zayed Cricket Stadium",
    "Subrata Roy Sahara Stadium": "Maharashtra Cricket Association Stadium",
    "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium": "Ekana Cricket Stadium",
    "Dr YS Rajasekhara Reddy ACA-VDCA Cricket Stadium": "ACA-VDCA Cricket Stadium",
    "Andhra Cricket Association-Visakhapatnam District Cricket Association Stadium":
        "ACA-VDCA Cricket Stadium",
    "De Beers Diamond Oval": "Diamond Oval",
    "New Wanderers Stadium": "Wanderers Stadium",
    "OUTsurance Oval": "Mangaung Oval",
    "Vidarbha Cricket Association Stadium": "VCA Stadium",
}

CITY_ALIASES: dict[str, str] = {"Bangalore": "Bengaluru", "Chandigarh": "Mohali"}

# Fallback for Cricsheet season labels when no date is available
SEASON_LABELS: dict[str, int] = {"2007/08": 2008, "2009/10": 2010, "2020/21": 2020}


def normalise_team(name: str | None) -> str | None:
    """Map any historical franchise name to its current name."""
    if name is None or (isinstance(name, float) and name != name):
        return None
    name = " ".join(str(name).split())
    return TEAM_ALIASES.get(name, name)


def team_short(name: str) -> str:
    return TEAM_SHORT.get(normalise_team(name) or "", name)


def normalise_venue(name: str | None) -> str | None:
    """Collapse spelling variants, city suffixes and old names of a ground."""
    if name is None or (isinstance(name, float) and name != name):
        return None
    v = " ".join(str(name).split())
    # "M.Chinnaswamy" -> "M Chinnaswamy", "Dr. Y.S." -> "Dr YS"
    v = re.sub(r"\bM\.\s*", "M ", v)
    v = v.replace("Dr. Y.S. ", "Dr YS ").replace("Dr. ", "Dr ")
    parts = [p.strip() for p in v.split(",")]
    while len(parts) > 1 and parts[-1] in PLACE_SUFFIXES:
        parts.pop()
    v = ", ".join(parts)
    return VENUE_RENAMES.get(v, v)


def normalise_city(city: str | None) -> str | None:
    if city is None or (isinstance(city, float) and city != city):
        return None
    city = str(city).strip()
    return CITY_ALIASES.get(city, city)


def normalise_season(label: str | int | None, match_date: str | date | None = None) -> int:
    """Return the IPL season as a calendar year.

    The match date wins when present. Otherwise use the label: plain years
    pass through and split labels use the lookup table above.
    """
    if match_date is not None and match_date == match_date:
        if isinstance(match_date, (date, datetime)):
            return match_date.year
        return int(str(match_date).replace("/", "-")[:4])
    if label is None:
        raise ValueError("need a season label or a match date")
    s = str(label).strip()
    if s in SEASON_LABELS:
        return SEASON_LABELS[s]
    if re.fullmatch(r"\d{4}", s):
        return int(s)
    raise ValueError(f"unrecognised season label {label!r}")


def era_of(season: int) -> str:
    """Bucket seasons into eras used for the toss and scoring comparisons.

    2023 is the first season with the Impact Player rule, which changed how
    teams bat, so it starts its own era.
    """
    if season <= 2012:
        return "2008-12"
    if season <= 2017:
        return "2013-17"
    if season <= 2022:
        return "2018-22"
    return "2023-26 (Impact Player)"


ERA_ORDER = ["2008-12", "2013-17", "2018-22", "2023-26 (Impact Player)"]
