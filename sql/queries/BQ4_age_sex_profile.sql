-- ============================================================
-- BQ4 — Age / sex profile of casualties vs drivers
-- Compares the age-band distribution of casualties against the
-- age-band distribution of drivers, split by sex.
--
-- NOTE: DfT reports casualty age and driver age on DIFFERENT band
-- schemes (casualty: 0-5, 6-10, ..., 76+; driver: 0-5, 6-10, 11-15,
-- 16-20, 21-25, 26-35, 36-45, 46-55, 56-65, 66-75, Over 75). To make
-- them comparable we use a grid whose edges ARE driver band edges:
-- 0-15, 16-25, 26-35, 36-45, 46+, Unknown. Casualties are banded from
-- the raw `age` (exact); drivers' bands merge cleanly into it, so no
-- band straddles a boundary.
-- Skills: CTE, FULL OUTER JOIN on a shared key, percentage share
-- ============================================================
WITH casualty_profile AS (
    SELECT
        CASE
            WHEN age IS NULL THEN 'Unknown'
            WHEN age <= 15 THEN '0-15'
            WHEN age <= 25 THEN '16-25'
            WHEN age <= 35 THEN '26-35'
            WHEN age <= 45 THEN '36-45'
            ELSE '46+'
        END AS age_band,
        sex,
        COUNT(*) AS n
    FROM fact_casualty
    GROUP BY 1, sex
),
driver_profile AS (
    SELECT
        CASE driver_age_band
            WHEN '0-5'     THEN '0-15'
            WHEN '6-10'    THEN '0-15'
            WHEN '11-15'   THEN '0-15'
            WHEN '16-20'   THEN '16-25'
            WHEN '21-25'   THEN '16-25'
            WHEN '26-35'   THEN '26-35'
            WHEN '36-45'   THEN '36-45'
            WHEN '46-55'   THEN '46+'
            WHEN '56-65'   THEN '46+'
            WHEN '66-75'   THEN '46+'
            WHEN 'Over 75' THEN '46+'
            ELSE 'Unknown'
        END AS age_band,
        driver_sex AS sex,
        COUNT(*)   AS n
    FROM fact_vehicle
    GROUP BY 1, driver_sex
),
combined AS (
    SELECT
        COALESCE(c.age_band, d.age_band) AS age_band,
        COALESCE(c.sex, d.sex)           AS sex,
        COALESCE(c.n, 0)                 AS casualties,
        COALESCE(d.n, 0)                 AS drivers
    FROM casualty_profile c
    FULL OUTER JOIN driver_profile d
        ON c.age_band = d.age_band AND c.sex = d.sex
)
SELECT
    age_band,
    sex,
    casualties,
    drivers,
    ROUND(100.0 * casualties / NULLIF(SUM(casualties) OVER (PARTITION BY sex), 0), 1) AS pct_of_sex_casualties,
    ROUND(100.0 * drivers    / NULLIF(SUM(drivers)    OVER (PARTITION BY sex), 0), 1) AS pct_of_sex_drivers
FROM combined
ORDER BY sex,
    CASE age_band
        WHEN '0-15'  THEN 1
        WHEN '16-25' THEN 2
        WHEN '26-35' THEN 3
        WHEN '36-45' THEN 4
        WHEN '46+'   THEN 5
        ELSE 6
    END;
