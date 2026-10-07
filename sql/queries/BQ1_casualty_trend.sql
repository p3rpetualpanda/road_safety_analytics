-- ============================================================
-- BQ1 — Trend in fatal / serious / slight casualties over time
-- Grain: one row per (year, month)
-- Skills: CTE, conditional aggregation, window function (MoM)
-- ============================================================
WITH monthly AS (
    SELECT
        d.year,
        d.month,
        d.month_name,
        c.severity,
        COUNT(*) AS casualties
    FROM fact_casualty c
    JOIN dim_date d ON d.date_key = c.date_key
    GROUP BY d.year, d.month, d.month_name, c.severity
),
pivoted AS (
    SELECT
        year,
        month,
        month_name,
        SUM(CASE WHEN severity = 1 THEN casualties ELSE 0 END) AS fatal,
        SUM(CASE WHEN severity = 2 THEN casualties ELSE 0 END) AS serious,
        SUM(CASE WHEN severity = 3 THEN casualties ELSE 0 END) AS slight,
        SUM(casualties)                                        AS total
    FROM monthly
    GROUP BY year, month, month_name
)
SELECT
    year,
    month,
    month_name,
    fatal,
    serious,
    slight,
    total,
    -- Serious/fatal share of all casualties (the headline KPI)
    ROUND(100.0 * (fatal + serious) / NULLIF(total, 0), 1) AS serious_fatal_pct,
    -- Month-over-month change in serious+fatal
    (fatal + serious)
        - LAG(fatal + serious, 1) OVER (ORDER BY year, month) AS mom_change_serious_fatal
FROM pivoted
ORDER BY year, month;
