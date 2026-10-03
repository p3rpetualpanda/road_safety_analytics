-- ============================================================
-- BQ5 — Vehicle types and manoeuvres most associated with
--       serious / fatal outcomes
-- For each vehicle type and manoeuvre, the share of its
-- accidents that produced a serious or fatal casualty.
-- Skills: CTE, conditional aggregation, RANK()
-- ============================================================
WITH vehicle_outcome AS (
    SELECT
        v.vehicle_type,
        v.manoeuvre,
        COUNT(DISTINCT v.accident_index) AS accidents,
        COUNT(DISTINCT CASE WHEN c.severity IN (1, 2) THEN v.accident_index END) AS serious_fatal_accidents
    FROM fact_vehicle v
    LEFT JOIN fact_casualty c ON c.accident_index = v.accident_index
    GROUP BY v.vehicle_type, v.manoeuvre
)
SELECT
    vehicle_type,
    manoeuvre,
    accidents,
    serious_fatal_accidents,
    ROUND(100.0 * serious_fatal_accidents / NULLIF(accidents, 0), 1) AS pct_serious_fatal,
    RANK() OVER (ORDER BY serious_fatal_accidents::numeric / NULLIF(accidents, 0) DESC) AS rank
FROM vehicle_outcome
WHERE accidents >= 20          -- reliability floor
ORDER BY pct_serious_fatal DESC
LIMIT 25;
