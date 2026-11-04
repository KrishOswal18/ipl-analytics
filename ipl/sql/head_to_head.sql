-- Head-to-head wins between every pair of franchises (decided matches only).
SELECT
    LEAST(team_a, team_b)    AS team_1,
    GREATEST(team_a, team_b) AS team_2,
    COUNT(*)                 AS matches,
    SUM(CASE WHEN winner = LEAST(team_a, team_b) THEN 1 ELSE 0 END)    AS team_1_wins,
    SUM(CASE WHEN winner = GREATEST(team_a, team_b) THEN 1 ELSE 0 END) AS team_2_wins
FROM matches
WHERE decided
GROUP BY 1, 2
ORDER BY matches DESC;
