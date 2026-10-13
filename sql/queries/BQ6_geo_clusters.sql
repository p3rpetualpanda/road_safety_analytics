-- ============================================================
-- BQ6 — Geographic high-risk clusters
-- Aggregates serious/fatal casualties into 0.1-degree grid cells
-- (a lightweight proxy for clustering without PostGIS) and ranks
-- the densest cells.
-- Uses each collision's own coordinates (fact_accident.lat/long);
-- dim_location lat/long is only one representative point per group.
-- Skills: CTE, numeric binning, window function, ordering
-- ============================================================
WITH grid AS (
    SELECT
        ROUND(a.lat  / 0.1) * 0.1 AS grid_lat,
        ROUND(a.long / 0.1) * 0.1 AS grid_long,
        l.district,
        c.casualty_rec,
        c.severity
    FROM fact_casualty c
    JOIN fact_accident a ON a.accident_index = c.accident_index
    JOIN dim_location l  ON l.location_key = a.location_key
    WHERE a.lat IS NOT NULL AND a.long IS NOT NULL
)
SELECT
    grid_lat,
    grid_long,
    MODE() WITHIN GROUP (ORDER BY district) AS main_district,
    COUNT(*) AS total_casualties,
    COUNT(CASE WHEN severity IN (1, 2) THEN 1 END) AS serious_fatal,
    RANK() OVER (ORDER BY COUNT(CASE WHEN severity IN (1, 2) THEN 1 END) DESC) AS risk_rank
FROM grid
GROUP BY grid_lat, grid_long
HAVING COUNT(CASE WHEN severity IN (1, 2) THEN 1 END) >= 5   -- reliability floor
ORDER BY serious_fatal DESC
LIMIT 25;
