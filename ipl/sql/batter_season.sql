-- Season batting table with strike-rate and run rankings computed by window
-- functions. Only batters who faced at least $min_balls balls are ranked.
WITH per_season AS (
    SELECT
        season,
        batter,
        ARG_MAX(batting_team, balls)              AS team,
        COUNT(*)                                  AS innings,
        SUM(runs)                                 AS runs,
        SUM(balls)                                AS balls,
        SUM(CASE WHEN out THEN 1 ELSE 0 END)      AS dismissals,
        SUM(fours)                                AS fours,
        SUM(sixes)                                AS sixes,
        SUM(CASE WHEN runs >= 50 THEN 1 ELSE 0 END) AS fifties_plus
    FROM batting_innings
    GROUP BY season, batter
)
SELECT
    *,
    runs * 100.0 / balls                                        AS strike_rate,
    runs * 1.0 / NULLIF(dismissals, 0)                          AS average,
    (fours * 4 + sixes * 6) * 1.0 / NULLIF(runs, 0)             AS boundary_run_share,
    RANK() OVER (PARTITION BY season ORDER BY runs * 1.0 / balls DESC) AS sr_rank,
    RANK() OVER (PARTITION BY season ORDER BY runs DESC)        AS runs_rank,
    COUNT(*) OVER (PARTITION BY season)                         AS qualified_in_season
FROM per_season
WHERE balls >= $min_balls
ORDER BY season, sr_rank;
