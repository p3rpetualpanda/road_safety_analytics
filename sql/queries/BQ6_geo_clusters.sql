-- ============================================================
-- BQ6 — Geographic high-risk clusters
-- Aggregates serious/fatal casualties into 0.1-degree grid cells
-- (a lightweight proxy for clustering without PostGIS) and ranks
-- the densest cells.
-- Skills: CTE, numeric binning, window function, ordering
-- ============================================================
WITH grid AS (
    SELECT
        ROUND(l.lat  / 0.1) * 0.1 AS grid_lat,
        ROUND(l.long / 0.1) * 0.1 AS grid_long,
        l.district,
        c.casualty_rec,
        c.severity
    FROM fact_casualty c
    JOIN dim_location l ON l.location_key = c.location_key
    WHERE l.lat IS NOT NULL AND l.long IS NOT NULL
)
SELECT
    grid_lat,
    grid_long,
    MIN(district) AS example_district,
    COUNT(*) AS total_casualties,
    COUNT(CASE WHEN severity IN (1, 2) THEN 1 END) AS serious_fatal,
    RANK() OVER (ORDER BY COUNT(CASE WHEN severity IN (1, 2) THEN 1 END) DESC) AS risk_rank
FROM grid
GROUP BY grid_lat, grid_long
HAVING COUNT(CASE WHEN severity IN (1, 2) THEN 1 END) >= 5   -- reliability floor
ORDER BY serious_fatal DESC
LIMIT 25;
