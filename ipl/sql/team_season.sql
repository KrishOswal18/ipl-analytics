-- Win/loss record and net run rate for every team in every season.
-- No-result games count as played but not won or lost, and are left out of NRR
-- (that is how the IPL points table works).
WITH appearances AS (
    SELECT season, match_id, team_a AS team, winner, decided FROM matches
    UNION ALL
    SELECT season, match_id, team_b AS team, winner, decided FROM matches
),
record AS (
    SELECT
        season,
        team,
        COUNT(*)                                             AS played,
        SUM(CASE WHEN decided AND winner = team THEN 1 ELSE 0 END)  AS won,
        SUM(CASE WHEN decided AND winner <> team THEN 1 ELSE 0 END) AS lost,
        SUM(CASE WHEN NOT decided THEN 1 ELSE 0 END)         AS no_result
    FROM appearances
    GROUP BY season, team
),
rates AS (
    SELECT
        season,
        team,
        SUM(runs_for)      * 6.0 / SUM(nrr_balls_for)      AS run_rate_for,
        SUM(runs_against)  * 6.0 / SUM(nrr_balls_against)  AS run_rate_against,
        AVG(run_rate_diff)                                 AS avg_run_rate_diff
    FROM team_matches
    WHERE decided
    GROUP BY season, team
)
SELECT
    r.season,
    r.team,
    r.played,
    r.won,
    r.lost,
    r.no_result,
    r.won * 1.0 / NULLIF(r.won + r.lost, 0)         AS win_pct,
    t.run_rate_for,
    t.run_rate_against,
    t.run_rate_for - t.run_rate_against             AS nrr,
    t.avg_run_rate_diff
FROM record r
LEFT JOIN rates t USING (season, team)
ORDER BY r.season, win_pct DESC;
