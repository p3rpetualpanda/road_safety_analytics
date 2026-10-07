-- ============================================================
-- BQ4 — Age / sex profile of casualties vs drivers
-- Compares the age-band distribution of casualties against the
-- age-band distribution of drivers, split by sex.
--
-- NOTE: DfT reports casualty age and driver age on DIFFERENT band
-- schemes (casualty: 0-5, 6-10, ..., 76+; driver: 0-5, 6-10, 11-15,
-- 16-20, 21-25, 26-35, 36-45, 46-55, 56-65, 66-75, Over 75). To make
-- them comparable we map BOTH onto a common reporting grid: 0-17,
-- 18-24, 25-34, 35-44, 45+, Unknown. Casualties are banded from the
-- raw `age` (exact). Drivers are mapped from their band label; bands
-- that straddle a grid boundary are placed in the cell holding most
-- of their range (e.g. 16-20 -> 18-24, 26-35 -> 25-34). Driver age is
-- reported up to "Over 75", so the 45+ cell now includes drivers.
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
            WHEN '0-5'     THEN '0-17'
            WHEN '6-10'    THEN '0-17'
            WHEN '11-15'   THEN '0-17'
            WHEN '16-20'   THEN '18-24'
            WHEN '21-25'   THEN '18-24'
            WHEN '26-35'   THEN '25-34'
            WHEN '36-45'   THEN '35-44'
            WHEN '46-55'   THEN '45+'
            WHEN '56-65'   THEN '45+'
            WHEN '66-75'   THEN '45+'
            WHEN 'Over 75' THEN '45+'
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
