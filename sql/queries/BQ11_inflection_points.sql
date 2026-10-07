-- ============================================================
-- BQ11 — Inflection points: months where serious+fatal
--        casualties deviate sharply from the trailing 12-month
--        moving average (candidate spikes / dips worth a closer
--        look, e.g. a heatwave, a policy change, a data revision).
-- Grain: one row per month (2021–2025), only months with a
--        full 12-month window and |deviation| >= 10%
-- Skills: CTE, window functions (AVG OVER, LAG), conditional
--         filtering, ordering by magnitude of deviation
-- ============================================================
WITH monthly AS (
    SELECT
        d.year,
        d.month,
        d.month_name,
        COUNT(CASE WHEN c.severity IN (1, 2) THEN 1 END) AS serious_fatal
    FROM fact_casualty c
    JOIN dim_date d ON d.date_key = c.date_key
    GROUP BY d.year, d.month, d.month_name
),
with_ma AS (
    SELECT
        year,
        month,
        month_name,
        serious_fatal,
        AVG(serious_fatal) OVER (
            ORDER BY year, month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS ma_12m,
        COUNT(*) OVER (
            ORDER BY year, month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS window_rows
    FROM monthly
)
SELECT
    year,
    month,
    month_name,
    serious_fatal,
    ROUND(ma_12m, 1) AS ma_12m,
    serious_fatal - ma_12m AS deviation,
    ROUND(100.0 * (serious_fatal - ma_12m) / NULLIF(ma_12m, 0), 1) AS deviation_pct,
    CASE
        WHEN serious_fatal > ma_12m THEN 'spike'
        ELSE 'dip'
    END AS direction
FROM with_ma
WHERE window_rows = 12                       -- only full 12-month windows
  AND ABS(100.0 * (serious_fatal - ma_12m) / NULLIF(ma_12m, 0)) >= 10.0
ORDER BY ABS(100.0 * (serious_fatal - ma_12m) / NULLIF(ma_12m, 0)) DESC;
