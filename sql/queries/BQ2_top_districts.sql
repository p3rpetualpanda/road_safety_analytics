-- ============================================================
-- BQ2 — Districts / road classes with the highest serious-injury
--       rate per accident
-- Definition: (serious + fatal casualties) / accidents, per district
-- and per road class. Ranked with a window function.
-- Skills: CTE, division, RANK(), HAVING filter for reliability
-- ============================================================
WITH district_stats AS (
    SELECT
        l.district,
        COUNT(DISTINCT a.accident_index) AS accidents,
        COUNT(c.casualty_rec)            AS total_casualties,
        COUNT(CASE WHEN c.severity IN (1, 2) THEN c.casualty_rec END) AS serious_fatal
    FROM fact_accident a
    JOIN dim_location l ON l.location_key = a.location_key
    LEFT JOIN fact_casualty c ON c.accident_index = a.accident_index
    GROUP BY l.district
),
road_class_stats AS (
    SELECT
        l.road_class,
        COUNT(DISTINCT a.accident_index) AS accidents,
        COUNT(CASE WHEN c.severity IN (1, 2) THEN c.casualty_rec END) AS serious_fatal
    FROM fact_accident a
    JOIN dim_location l ON l.location_key = a.location_key
    LEFT JOIN fact_casualty c ON c.accident_index = a.accident_index
    GROUP BY l.road_class
)
SELECT
    'district' AS dimension,
    district   AS name,
    accidents,
    serious_fatal,
    ROUND(serious_fatal::numeric / NULLIF(accidents, 0), 3) AS serious_per_accident,
    RANK() OVER (ORDER BY serious_fatal::numeric / NULLIF(accidents, 0) DESC) AS rank
FROM district_stats
WHERE accidents >= 50          -- reliability floor
UNION ALL
SELECT
    'road_class' AS dimension,
    road_class   AS name,
    accidents,
    serious_fatal,
    ROUND(serious_fatal::numeric / NULLIF(accidents, 0), 3) AS serious_per_accident,
    RANK() OVER (ORDER BY serious_fatal::numeric / NULLIF(accidents, 0) DESC) AS rank
FROM road_class_stats
WHERE accidents >= 50
ORDER BY dimension, rank;
