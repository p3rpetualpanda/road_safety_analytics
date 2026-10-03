-- ============================================================
-- BQ3 — How casualty severity varies by weather, lighting,
--       and road surface
-- Output: % of casualties that are serious/fatal, per condition.
-- Skills: conditional aggregation, percentage share, ordering
-- ============================================================
WITH base AS (
    SELECT
        a.weather,
        a.lighting,
        a.road_surface,
        c.severity
    FROM fact_casualty c
    JOIN fact_accident a ON a.accident_index = c.accident_index
)
SELECT
    'weather' AS factor,
    weather   AS value,
    COUNT(*)  AS casualties,
    COUNT(CASE WHEN severity IN (1, 2) THEN 1 END) AS serious_fatal,
    ROUND(100.0 * COUNT(CASE WHEN severity IN (1, 2) THEN 1 END) / COUNT(*), 1) AS pct_serious_fatal
FROM base
GROUP BY weather

UNION ALL

SELECT
    'lighting' AS factor,
    lighting   AS value,
    COUNT(*)  AS casualties,
    COUNT(CASE WHEN severity IN (1, 2) THEN 1 END) AS serious_fatal,
    ROUND(100.0 * COUNT(CASE WHEN severity IN (1, 2) THEN 1 END) / COUNT(*), 1) AS pct_serious_fatal
FROM base
GROUP BY lighting

UNION ALL

SELECT
    'road_surface' AS factor,
    road_surface   AS value,
    COUNT(*)  AS casualties,
    COUNT(CASE WHEN severity IN (1, 2) THEN 1 END) AS serious_fatal,
    ROUND(100.0 * COUNT(CASE WHEN severity IN (1, 2) THEN 1 END) / COUNT(*), 1) AS pct_serious_fatal
FROM base
GROUP BY road_surface

ORDER BY factor, pct_serious_fatal DESC;
