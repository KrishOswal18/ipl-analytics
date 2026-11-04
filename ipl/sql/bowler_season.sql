-- Season bowling table. Economy = runs conceded per over, ranked among
-- bowlers with at least $min_balls legal deliveries.
WITH per_season AS (
    SELECT
        season,
        bowler,
        ARG_MAX(bowling_team, legal_balls) AS team,
        COUNT(*)            AS innings,
        SUM(legal_balls)    AS balls,
        SUM(runs_conceded)  AS runs_conceded,
        SUM(wickets)        AS wickets,
        SUM(dots)           AS dots
    FROM bowling_innings
    GROUP BY season, bowler
)
SELECT
    *,
    runs_conceded * 6.0 / balls                               AS economy,
    balls * 1.0 / NULLIF(wickets, 0)                          AS balls_per_wicket,
    dots * 1.0 / balls                                        AS dot_pct,
    RANK() OVER (PARTITION BY season ORDER BY runs_conceded * 1.0 / balls ASC) AS economy_rank,
    RANK() OVER (PARTITION BY season ORDER BY wickets DESC)   AS wickets_rank
FROM per_season
WHERE balls >= $min_balls
ORDER BY season, economy_rank;
