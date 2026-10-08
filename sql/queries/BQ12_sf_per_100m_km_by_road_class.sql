-- ============================================================
-- BQ12 — Serious+fatal casualties per 100 million vehicle-km,
--        by road class (national, GB).
-- Grain: one row per year × road class (2021–2025)
-- Exposure source: TRA0202 (DfT Road Traffic Estimates,
--   billion vehicle-km by road class, normalised to million
--   vehicle-km in the ETL).
-- Rate = (S/F casualties / vehicle_km_million) × 100
-- ============================================================
WITH sf_by_year AS (
    SELECT
        d.year,
        COUNT(*) AS serious_fatal
    FROM fact_casualty c
    JOIN dim_date d ON d.date_key = c.date_key
    WHERE c.severity IN (1, 2)
    GROUP BY d.year
),
exposure AS (
    SELECT
        year,
        road_class,
        vehicle_km_million
    FROM exposure_vehicle_km
    WHERE source_table = 'TRA0202'
      AND geo_code = 'GB'
      AND vehicle_type = 'All'
)
SELECT
    e.year,
    e.road_class,
    s.serious_fatal,
    e.vehicle_km_million,
    ROUND((s.serious_fatal::NUMERIC / e.vehicle_km_million) * 100, 4)
        AS sf_per_100m_km
FROM exposure e
JOIN sf_by_year s ON s.year = e.year
ORDER BY e.year, e.road_class;
