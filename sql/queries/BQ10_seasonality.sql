-- ============================================================
-- BQ10 — Seasonality: month-of-year patterns in casualties,
--        pooled across all years (2021–2025).
-- Grain: one row per month (1–12)
-- Skills: CTE, conditional aggregation, window function
--         (share of annual total per month)
-- ============================================================
WITH monthly AS (
    SELECT
        d.month,
        d.month_name,
        COUNT(*) AS total_casualties,
        COUNT(CASE WHEN c.severity = 1 THEN 1 END) AS fatal,
        COUNT(CASE WHEN c.severity IN (1, 2) THEN 1 END) AS serious_fatal
    FROM fact_casualty c
    JOIN dim_date d ON d.date_key = c.date_key
    GROUP BY d.month, d.month_name
),
totals AS (
    SELECT
        SUM(total_casualties) AS annual_total,
        SUM(serious_fatal)    AS annual_serious_fatal
    FROM monthly
)
SELECT
    m.month,
    m.month_name,
    m.total_casualties,
    m.fatal,
    m.serious_fatal,
    ROUND(100.0 * m.serious_fatal / NULLIF(m.total_casualties, 0), 1) AS serious_fatal_pct,
    -- Share of the (pooled) annual total that falls in this month
    ROUND(100.0 * m.total_casualties / NULLIF(t.annual_total, 0), 2) AS share_of_annual_pct,
    -- Index vs the monthly average (100 = exactly average; >100 = above)
    ROUND(
        100.0 * m.total_casualties
            / NULLIF(t.annual_total / 12.0, 0),
        1
    ) AS seasonality_index
FROM monthly m
CROSS JOIN totals t
ORDER BY m.month;
