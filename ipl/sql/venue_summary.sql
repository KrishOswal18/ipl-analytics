-- How each ground plays: chasing success, first innings par score, toss effect.
-- Only decided matches; grounds with fewer than $min_matches games are dropped
-- because a 3 game sample says nothing.
SELECT
    venue,
    MAX(city)                                                 AS city,
    COUNT(*)                                                  AS matches,
    MIN(season)                                               AS first_season,
    MAX(season)                                               AS last_season,
    AVG(CASE WHEN bat_first_won = 1 THEN 0.0 ELSE 1.0 END)    AS chase_win_pct,
    AVG(first_innings_runs)                                   AS avg_first_innings,
    MEDIAN(first_innings_runs)                                AS median_first_innings,
    AVG(toss_winner_won)                                      AS toss_winner_win_pct,
    AVG(CASE WHEN toss_decision = 'field' THEN 1.0 ELSE 0.0 END) AS field_first_pct
FROM matches
WHERE decided
GROUP BY venue
HAVING COUNT(*) >= $min_matches
ORDER BY matches DESC;
