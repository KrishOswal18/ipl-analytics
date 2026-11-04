# IPL Analytics: 19 seasons, ball by ball

I took every IPL match from 2008 to 2026 (1,243 matches, 295,732 deliveries) from Cricsheet's raw
ball-by-ball files and worked through a few questions I had argued about with friends for years:
does winning the toss actually help, which grounds favour chasing, who are the fastest and most
consistent batters, and can you put a sensible number on a chase while it is happening?

The project has three parts:

* a Python package (`ipl/`) that downloads, cleans and models the data, with SQL in DuckDB and pytest tests
* a notebook (`notebooks/analysis.ipynb`) that tells the story from raw CSV to conclusions, with 21 charts
* a static dashboard (`web/`, React + TypeScript + Recharts) that reads exported JSON and runs the
  win probability model in the browser

This is v2 of my earlier [ipl-match-predictor](https://github.com/KrishOswal18/ipl-match-predictor).
The section [What I fixed from my first version](#what-i-fixed-from-my-first-version) explains what changed and what it was worth.

## Data

[Cricsheet](https://cricsheet.org) IPL data in the CSV2 format (`ipl_male_csv2.zip`): one file of
deliveries per match plus a match info file with toss, result, venue and players.
`python -m ipl download` fetches it into `data/raw/` (gitignored, so the repo stays small).

Cricsheet data is released under the Open Data Commons Attribution License (ODC-By 1.0).

## Cleaning: making 19 seasons line up

The raw files are not consistent across seasons. All the rules live in `ipl/normalise.py` as plain
dictionaries and are covered by tests.

| Problem | Example | Fix |
|---|---|---|
| Renamed franchises | Delhi Daredevils, Kings XI Punjab, Royal Challengers Bangalore | mapped to Delhi Capitals, Punjab Kings, Royal Challengers Bengaluru. 19 raw names become 15 franchises |
| Different franchises, similar names | Deccan Chargers vs Sunrisers Hyderabad | kept separate on purpose (different owners), same for Gujarat Lions vs Gujarat Titans |
| Venue spelling and city suffixes | "M.Chinnaswamy Stadium", "M Chinnaswamy Stadium, Bengaluru" | punctuation fixed, city or locality suffix stripped |
| Renamed grounds | Feroz Shah Kotla, Sardar Patel Stadium (Motera) | Arun Jaitley Stadium, Narendra Modi Stadium. 83 raw venue strings become 36 grounds |
| Season labels | "2007/08", "2009/10", "2020/21" | season taken from the match date's year |
| Ties | 16 tied matches decided by super overs | super-over winner counted as match winner, super-over balls excluded from batting and bowling stats |
| No results and rain | 9 no-results, 23 D/L results | no-results excluded from win rates and NRR, D/L matches excluded from the win probability model |

A check in the tests confirms the cleaning: for every full-length chase, my first innings total plus
one equals the target Cricsheet records, and the venue from the info file matches the venue from the
ball-by-ball file after normalising.

## Method

```
download.py   fetch + unzip Cricsheet CSV2
ingest.py     read info files and deliveries into pandas
normalise.py  team, venue, city and season alias maps
tables.py     build deliveries, innings, matches, team_matches, batting_innings, bowling_innings -> DuckDB
sql/*.sql     season summary, team-season records + NRR, venue summary, batter and bowler season
              rankings (RANK() OVER (PARTITION BY season ...)), head to head
features.py   run rate, strike rate, NRR balls (bowled out = full quota), run rate differential,
              consistency metrics, rankings, chase state, Wilson interval
analysis.py   career tables and consistency on top of the SQL results
stats.py      toss tests
winprob.py    chase win probability model
legacy.py     reproduction of my v1 predictor and the corrected version
charts.py     21 matplotlib charts
export.py     compact JSON for the dashboard
```

Engineered features: per-match run rate differential and season net run rate (with the IPL rule
that a side bowled out is charged its full overs), phase run rates (powerplay, middle, death),
season and career strike-rate rankings, and a consistency index (share of innings with 25+ runs,
plus median score and the coefficient of variation of scores).

## Findings

**1. Scoring has exploded since 2023.** The average first innings total stayed between 150 and 172 from
2008 to 2022, then rose to 193 in 2026. 200+ totals went from 7 in 2008 to 38 in 2026, sixes per
match from 10.7 to 19.3. Powerplay scoring grew the most (7.4 to 9.5 runs an over, 2008 to 2012 vs
2023 to 2026). The timing matches the Impact Player rule introduced in 2023.

**2. Winning the toss on its own is not significant.** Exact binomial test, H0: P(toss winner wins) = 0.5.

| | Toss winner won | Rate | 95% CI | p-value |
|---|---|---|---|---|
| All decided matches | 634 / 1234 | 51.4% | 48.6% to 54.2% | 0.348 |
| Chose to field | 446 / 820 | 54.4% | 51.0% to 57.8% | 0.013 |
| Chose to bat | 188 / 414 | 45.4% | 40.7% to 50.2% | 0.069 |

No era is significant and the eras do not differ from each other (chi-square p = 0.95). With 1,234
matches the test could reliably detect only an edge of about 4 points, so the honest reading is "no
detectable effect", not "proven zero". No individual ground is significant after a Bonferroni correction.

**3. The real edge is chasing.** Bat vs field decisions lead to different outcomes (chi-square p = 0.0035),
and the chasing side won 54.5% of all decided matches (672 / 1234, p = 0.0019). Captains have worked
this out: fielding first went from 55% of tosses in 2008 to 82% in 2026. Interestingly the chasing
edge is smallest in the Impact Player era (52.4%, p = 0.44), when targets got bigger.

**4. Net run rate explains most of a season.** Across 166 team-seasons, season NRR and win % correlate
at r = 0.77 (R squared 0.59). Each +1.0 of NRR is worth about 21 points of win %.

**5. Grounds differ.** Among grounds with 20+ decided matches, chasing wins 65% at Sawai Mansingh
(Jaipur, 68 matches) and 64% at Sharjah, but only 45% at MCA Stadium Pune and 46% at Chepauk.

**6. Players.** Among batters with 500+ career balls, Andre Russell has the highest strike rate (174.2),
then Abhishek Sharma (171.3) and Heinrich Klaasen (166.7). The most consistent (30+ innings) is
B Sai Sudharsan, who reaches 25 in 67% of his innings with a median score of 43. Sunil Narine has
the best economy among the top wicket takers (6.79 with 207 wickets).

**7. Chase win probability model.** Logistic regression on the state after every legal ball of a
chase: runs needed, balls left, wickets left, required rate, two interaction features, and the
previous season's overall run rate as a measure of the scoring environment (known before the season,
so no leakage). The training window is chosen on 2024 as a validation season, and 2025 and 2026 are
only scored at the end.

| Model (tested on 2025 + 2026: 15,053 ball states, 138 chases) | Accuracy | Log-loss | Brier |
|---|---|---|---|
| Final model | 83.6% | 0.367 | 0.115 |
| Same model without the scoring level feature | 80.4% | 0.423 | 0.137 |
| Logistic regression on required run rate only | 79.9% | 0.438 | 0.142 |
| Constant: training chase win rate | 56.1% | 0.689 | 0.248 |

The scoring level feature came from looking at calibration. Without it the model was well calibrated
on its training seasons but underrated chasers in 2025 and 2026 (when it said 40%, chasers won about
60%), because a required rate of 10 an over is simply easier now than in 2012.

## What I fixed from my first version

My first project predicted the winner after the first innings with a random forest on Kaggle's
`deliveries.csv`. Looking back at it, five things were wrong:

1. **Leakage.** Each team's win rate was computed over all matches, including the ones in the test set.
2. **Random split.** Matches from the same season ended up in both train and test, which is not how a
   model predicting future games would be used.
3. **Wrong labels.** Winner was "team 2 if score2 > score1, else team 1", so every tie went to the side
   batting first and no-results were treated as results.
4. **Names not normalised.** Delhi Daredevils and Delhi Capitals were two different teams in the data,
   while the app offered only the new names, so the encoder and win rates did not match.
5. **Hardcoded win rates** in `app.py` and unpinned requirements with unused packages.

I reproduced v1 on the same Cricsheet data (`ipl/legacy.py`) and fixed one thing at a time:

| Version | Accuracy |
|---|---|
| v1 exactly as written, 2008 to 2022, random 80/20 split (mean of 20 splits) | 64.4% (sd 2.5) |
| v1 method on all seasons 2008 to 2026, random split | 65.1% |
| Real Cricsheet results and normalised names, still leaky, random split | 65.8% |
| Win rates only from matches before each game (no leakage), random split | 66.1% |
| Same random forest, trained to 2024, tested on 2025 and 2026 (144 matches) | 63.9% |
| Logistic regression on first innings score and wickets only, same holdout | 66.0% |
| Baseline: always pick the chasing side, same holdout | 56.9% |

What I learned: v1's labels were wrong for 20 matches, and 3 no-results were counted as results.
The leakage turned out to be small here (a career win rate barely moves when a few test games are
included), so v1's accuracy was not badly inflated, but it was also not better than a two-feature
logistic regression. With 144 test matches every number above has a 95% interval of about 8 points
either way, so the fair summary is "about 64 to 66%, and the simple model is as good as the complex
one". My v1 README also said 1,092 matches for 2008 to 2022; Cricsheet has 950 matches in those
seasons.

In v2 everything uses Cricsheet's own result fields, names are normalised once in one place,
evaluation is always by season, requirements are pinned, and the dashboard computes probabilities
from coefficients exported by the pipeline instead of hardcoded numbers.

## How to run

Python 3.11+ and Node 18+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m ipl run        # download, build DuckDB, run tests and model, save charts, export JSON
pytest                   # 63 tests

# re-run the notebook with outputs
jupyter nbconvert --to notebook --execute --inplace notebooks/analysis.ipynb

# dashboard
cd web
npm install
npm run dev              # http://localhost:5173
npm run build            # static site in web/dist
```

`python -m ipl run` takes about 30 seconds after the download. It writes:

* `data/processed/ipl.duckdb` (all tables, query it with any DuckDB client)
* `reports/figures/*.png` (21 charts)
* `web/public/data/*.json` (dashboard data, about 470 KB, committed so the site builds without Python)

## Deploying

The dashboard is a static Vite build, so Vercel deploys it with root directory `web`, build command
`npm run build` and output directory `dist`. Step by step instructions are in [DEPLOY.md](DEPLOY.md).

## Repository layout

```
ipl/                 Python package (pipeline, SQL, stats, model, charts, export)
  sql/               DuckDB queries
tests/               pytest
notebooks/           analysis.ipynb, executed with outputs
reports/figures/     21 PNG charts
web/                 React + TypeScript dashboard (Vite, Recharts)
  public/data/       exported JSON
data/raw, data/processed   created by the pipeline, gitignored
```

## Limitations

* Ball states inside one chase are correlated, so the model's ball-level accuracy overstates how many
  independent predictions it made. The 138 test chases are the real sample size.
* Venue results pool all seasons. A ground used mostly in high scoring years looks higher scoring.
* Consistency uses a fixed 25 run threshold, which favours top order batters over finishers who face few balls.

## Credits

Data from [Cricsheet](https://cricsheet.org) under ODC-By 1.0. Code under the MIT License.
