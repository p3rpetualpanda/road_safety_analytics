-- ============================================================
-- BQ4 — Age / sex profile of casualties vs drivers
-- Compares the age-band distribution of casualties against the
-- age-band distribution of drivers, split by sex.
--
-- NOTE: DfT reports casualty age and driver age on DIFFERENT band
-- schemes (casualty: 0-5, 6-10, ..., 76+; driver: 0-1, 2-5, ...,
-- 40-44). To make them comparable we map BOTH onto a common
-- reporting grid: 0-17, 18-24, 25-34, 35-44, 45+, Unknown.
-- Casualties are banded from the raw `age` (exact). Drivers are
-- mapped from their band label (one approximation: the 17-20 band
-- is placed in 18-24). Driver age is only reported up to 40-44,
-- so the 45+ cell has no drivers by design.
-- Skills: CTE, FULL OUTER JOIN on a shared key, percentage share
-- ============================================================
WITH casualty_profile AS (
    SELECT
        CASE
            WHEN age IS NULL THEN 'Unknown'
            WHEN age <= 17 THEN '0-17'
            WHEN age <= 24 THEN '18-24'
            WHEN age <= 34 THEN '25-34'
            WHEN age <= 44 THEN '35-44'
            ELSE '45+'
        END AS age_band,
        sex,
        COUNT(*) AS n
    FROM fact_casualty
    GROUP BY 1, sex
),
driver_profile AS (
    SELECT
        CASE driver_age_band
            WHEN '0-1'   THEN '0-17'
            WHEN '2-5'   THEN '0-17'
            WHEN '6-10'  THEN '0-17'
            WHEN '11-14' THEN '0-17'
            WHEN '15-17' THEN '0-17'
            WHEN '17-20' THEN '18-24'
            WHEN '21-24' THEN '18-24'
            WHEN '25-29' THEN '25-34'
            WHEN '30-34' THEN '25-34'
            WHEN '35-39' THEN '35-44'
            WHEN '40-44' THEN '35-44'
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
        WHEN '0-17'  THEN 1
        WHEN '18-24' THEN 2
        WHEN '25-34' THEN 3
        WHEN '35-44' THEN 4
        WHEN '45+'   THEN 5
        ELSE 6
    END;
