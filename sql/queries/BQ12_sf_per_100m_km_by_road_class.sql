-- ============================================================
-- BQ12 — Serious+fatal casualties per 100 million vehicle-km,
--        by road class (national, GB).
-- Grain: one row per year × road class (2021–2025)
-- Exposure source: TRA0202 (DfT Road Traffic Estimates,
--   billion vehicle-km by road class, normalised to million
--   vehicle-km in the ETL).
-- Rate = (S/F casualties ON THAT ROAD CLASS / its vehicle_km_million) × 100
-- Casualties are mapped to TRA0202's classes from the collision's
-- first road class + urban/rural flag: Motorway and A(M) -> Motorway;
-- A -> Rural/Urban 'A'; B, C, Unclassified -> Minor Rural/Urban.
-- Collisions with unknown class or urban/rural count only in All Roads.
-- ============================================================
WITH sf AS (
    SELECT
        d.year,
        CASE
            WHEN l.road_class IN ('Motorway', 'A(M)') THEN 'Major Roads: Motorway'
            WHEN l.road_class = 'A' AND l.urban_rural = 'Rural' THEN 'Major Roads: Rural ''A'' Roads'
            WHEN l.road_class = 'A' AND l.urban_rural = 'Urban' THEN 'Major Roads: Urban ''A'' Roads'
            WHEN l.road_class IN ('B', 'C', 'Unclassified') AND l.urban_rural = 'Rural' THEN 'Minor Roads: Rural'
            WHEN l.road_class IN ('B', 'C', 'Unclassified') AND l.urban_rural = 'Urban' THEN 'Minor Roads: Urban'
        END AS road_class
    FROM fact_casualty c
    JOIN dim_date d     ON d.date_key = c.date_key
    JOIN dim_location l ON l.location_key = c.location_key
    WHERE c.severity IN (1, 2)
),
sf_by_class AS (
    SELECT year, road_class, COUNT(*) AS serious_fatal
    FROM sf
    WHERE road_class IS NOT NULL
    GROUP BY year, road_class
    UNION ALL
    SELECT year, 'All Roads', COUNT(*)
    FROM sf
    GROUP BY year
),
exposure AS (
    SELECT
        year,
        road_class AS tra_label,
        vehicle_km_million
    FROM exposure_vehicle_km
    WHERE source_table = 'TRA0202'
      AND geo_code = 'GB'
      AND vehicle_type = 'All'
)
SELECT
    e.year,
    s.road_class,
    s.serious_fatal,
    e.vehicle_km_million,
    ROUND((s.serious_fatal::NUMERIC / e.vehicle_km_million) * 100, 4)
        AS sf_per_100m_km
FROM exposure e
-- TRA0202 labels carry "[note N]" suffixes, so match on the prefix
JOIN sf_by_class s
  ON s.year = e.year
 AND (e.tra_label = s.road_class OR e.tra_label LIKE s.road_class || ' [note%')
ORDER BY e.year, sf_per_100m_km DESC;
