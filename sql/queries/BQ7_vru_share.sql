-- ============================================================
-- BQ7 — Vulnerable road user (VRU) share of serious casualties,
--       and how it trends over time
-- VRU = pedestrian / cyclist / motorcyclist (vru_flag = TRUE).
-- Skills: CTE, conditional aggregation, window function (trend)
-- ============================================================
WITH yearly_vru AS (
    SELECT
        d.year,
        COUNT(*) AS serious_fatal_casualties,
        COUNT(CASE WHEN c.vru_flag THEN 1 END) AS vru_serious_fatal
    FROM fact_casualty c
    JOIN dim_date d ON d.date_key = c.date_key
    WHERE c.severity IN (1, 2)
    GROUP BY d.year
)
SELECT
    year,
    serious_fatal_casualties,
    vru_serious_fatal,
    ROUND(100.0 * vru_serious_fatal / NULLIF(serious_fatal_casualties, 0), 1) AS vru_share_pct,
    LAG(vru_serious_fatal, 1) OVER (ORDER BY year) AS prev_year_vru,
    vru_serious_fatal - LAG(vru_serious_fatal, 1) OVER (ORDER BY year) AS yoy_change
FROM yearly_vru
ORDER BY year;
