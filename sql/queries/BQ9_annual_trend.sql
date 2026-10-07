-- ============================================================
-- BQ9 — Annual trend in casualties with YoY change and a
--       12-month moving average of serious+fatal casualties.
-- Grain: one row per year (2021–2025)
-- Skills: CTE, conditional aggregation, window functions
--         (LAG for YoY, AVG OVER for a 12-month moving average)
-- ============================================================
WITH annual AS (
    SELECT
        d.year,
        COUNT(*) AS total_casualties,
        COUNT(CASE WHEN c.severity = 1 THEN 1 END) AS fatal,
        COUNT(CASE WHEN c.severity = 2 THEN 1 END) AS serious,
        COUNT(CASE WHEN c.severity IN (1, 2) THEN 1 END) AS serious_fatal
    FROM fact_casualty c
    JOIN dim_date d ON d.date_key = c.date_key
    GROUP BY d.year
),
monthly AS (
    SELECT
        d.year,
        d.month,
        COUNT(CASE WHEN c.severity IN (1, 2) THEN 1 END) AS serious_fatal
    FROM fact_casualty c
    JOIN dim_date d ON d.date_key = c.date_key
    GROUP BY d.year, d.month
),
moving AS (
    SELECT
        year,
        month,
        serious_fatal,
        AVG(serious_fatal) OVER (
            ORDER BY year, month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS ma_12m
    FROM monthly
)
SELECT
    a.year,
    a.total_casualties,
    a.fatal,
    a.serious,
    a.serious_fatal,
    ROUND(100.0 * a.serious_fatal / NULLIF(a.total_casualties, 0), 1) AS serious_fatal_pct,
    -- Year-over-year change in serious+fatal casualties
    a.serious_fatal - LAG(a.serious_fatal, 1) OVER (ORDER BY a.year) AS yoy_change_serious_fatal,
    ROUND(
        100.0 * (a.serious_fatal - LAG(a.serious_fatal, 1) OVER (ORDER BY a.year))
            / NULLIF(LAG(a.serious_fatal, 1) OVER (ORDER BY a.year), 0),
        1
    ) AS yoy_pct_serious_fatal,
    -- 12-month moving average of serious+fatal, sampled at each year's
    -- December (the most recent trailing-12-month window for that year)
    ROUND(m.ma_12m, 1) AS serious_fatal_ma_12m
FROM annual a
LEFT JOIN moving m
    ON m.year = a.year
   AND m.month = 12
ORDER BY a.year;
