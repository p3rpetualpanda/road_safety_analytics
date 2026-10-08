-- ============================================================
-- BQ13 — Serious+fatal casualties per 100,000 licensed
--        vehicles (national, UK).
-- Grain: one row per year (2021–2025)
-- Exposure source: VEH0101 (DfT Vehicle Licensing Statistics,
--   year-end Q4 snapshot, thousands of vehicles).
-- Rate = (S/F casualties / (vehicles_thousand × 1000)) × 100000
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
        vehicles_thousand
    FROM exposure_licensed_vehicles
    WHERE geo_name = 'United Kingdom'
      AND vehicle_type = 'Total'
)
SELECT
    e.year,
    s.serious_fatal,
    e.vehicles_thousand,
    ROUND(
        (s.serious_fatal::NUMERIC / (e.vehicles_thousand * 1000)) * 100000,
        4
    ) AS sf_per_100k_vehicles
FROM exposure e
JOIN sf_by_year s ON s.year = e.year
ORDER BY e.year;
