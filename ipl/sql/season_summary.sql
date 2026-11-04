-- One row per season: how much scoring there was and how captains used the toss.
WITH phase_rates AS (
    SELECT
        season,
        SUM(CASE WHEN phase = 'powerplay' THEN total_runs END) * 6.0
            / SUM(CASE WHEN phase = 'powerplay' AND is_legal THEN 1 END) AS rr_powerplay,
        SUM(CASE WHEN phase = 'middle' THEN total_runs END) * 6.0
            / SUM(CASE WHEN phase = 'middle' AND is_legal THEN 1 END)    AS rr_middle,
        SUM(CASE WHEN phase = 'death' THEN total_runs END) * 6.0
            / SUM(CASE WHEN phase = 'death' AND is_legal THEN 1 END)     AS rr_death,
        SUM(total_runs) * 6.0 / SUM(CASE WHEN is_legal THEN 1 END)        AS rr_overall,
        SUM(CASE WHEN is_six THEN 1 ELSE 0 END)                           AS sixes,
        SUM(CASE WHEN is_four THEN 1 ELSE 0 END)                          AS fours,
        COUNT(*)                                                          AS deliveries
    FROM deliveries
    WHERE NOT is_super_over
    GROUP BY season
),
match_stats AS (
    SELECT
        season,
        COUNT(*)                                                       AS matches,
        SUM(CASE WHEN decided THEN 1 ELSE 0 END)                       AS decided,
        AVG(first_innings_runs)                                        AS avg_first_innings,
        AVG(CASE WHEN toss_decision = 'field' THEN 1.0 ELSE 0.0 END)   AS field_first_pct,
        AVG(toss_winner_won)                                           AS toss_winner_win_pct,
        AVG(1 - bat_first_won)                                         AS chase_win_pct,
        SUM(CASE WHEN first_innings_runs >= 200 THEN 1 ELSE 0 END)     AS scores_200_plus
    FROM matches
    GROUP BY season
)
SELECT m.*, p.rr_powerplay, p.rr_middle, p.rr_death, p.rr_overall,
       p.sixes, p.fours, p.deliveries,
       p.sixes * 1.0 / m.matches AS sixes_per_match
FROM match_stats m
JOIN phase_rates p USING (season)
ORDER BY season;
