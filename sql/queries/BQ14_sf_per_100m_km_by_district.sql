-- ============================================================
-- BQ14 — Serious+fatal casualties per 100M vehicle-km
--        by local authority (district level).
-- Grain: one row per district (only districts with exposure data)
-- Exposure source: TRA8904 (DfT Road Traffic Estimates,
--   vehicle-km by local authority, million vehicle-km).
-- Rate = (S/F casualties / vehicle_km_million) × 100
-- Note: only districts present in both dim_location and
--   TRA8904 are included (~186 of 370 districts).
-- ============================================================
WITH sf_by_district AS (
    SELECT
        l.district,
        COUNT(*) AS serious_fatal
    FROM fact_accident a
    JOIN dim_location l ON l.location_key = a.location_key
    LEFT JOIN fact_casualty c ON c.accident_index = a.accident_index
    WHERE c.severity IN (1, 2)
    GROUP BY l.district
),
exposure_by_district AS (
    SELECT
        e.geo_code AS district,
        SUM(e.vehicle_km_million) AS vehicle_km_million
    FROM exposure_vehicle_km e
    WHERE e.source_table = 'TRA8904'
      AND e.year BETWEEN 2021 AND 2025
      AND e.geo_code IN (
          SELECT DISTINCT district
          FROM dim_location
          WHERE district IS NOT NULL AND district != ''
      )
    GROUP BY e.geo_code
)
SELECT
    e.district,
    s.serious_fatal,
    e.vehicle_km_million,
    ROUND(
        (s.serious_fatal::NUMERIC / e.vehicle_km_million) * 100,
        4
    ) AS sf_per_100m_km
FROM exposure_by_district e
JOIN sf_by_district s ON s.district = e.district
ORDER BY sf_per_100m_km DESC;
