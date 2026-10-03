-- ============================================================
-- BQ1 — Trend in fatal / serious / slight casualties over time
-- Grain: one row per (year, severity)
-- Skills: CTE, conditional aggregation, window function (YoY)
-- ============================================================
WITH yearly AS (
    SELECT
        d.year,
        c.severity,
        COUNT(*) AS casualties
    FROM fact_casualty c
    JOIN dim_date d ON d.date_key = c.date_key
    GROUP BY d.year, c.severity
),
pivoted AS (
    SELECT
        year,
        SUM(CASE WHEN severity = 1 THEN casualties ELSE 0 END) AS fatal,
        SUM(CASE WHEN severity = 2 THEN casualties ELSE 0 END) AS serious,
        SUM(CASE WHEN severity = 3 THEN casualties ELSE 0 END) AS slight,
        SUM(casualties)                                        AS total
    FROM yearly
    GROUP BY year
)
SELECT
    year,
    fatal,
    serious,
    slight,
    total,
    -- Year-over-year change in serious+fatal (the headline KPI)
    LAG(fatal + serious, 1) OVER (ORDER BY year) AS prev_serious_fatal,
    (fatal + serious)
        - LAG(fatal + serious, 1) OVER (ORDER BY year) AS yoy_change_serious_fatal
FROM pivoted
ORDER BY year;
