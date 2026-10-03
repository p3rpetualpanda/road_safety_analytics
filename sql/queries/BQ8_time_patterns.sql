-- ============================================================
-- BQ8 — Time-of-day / day-of-week patterns in severity
-- Two views: (a) by hour of day, (b) by day of week.
-- Shows the % of casualties that are serious/fatal per bucket.
-- Skills: CTE, EXTRACT(), conditional aggregation, ordering
-- ============================================================
WITH by_hour AS (
    SELECT
        EXTRACT(HOUR FROM a.accident_time) AS hour,
        COUNT(*) AS casualties,
        COUNT(CASE WHEN c.severity IN (1, 2) THEN 1 END) AS serious_fatal
    FROM fact_casualty c
    JOIN fact_accident a ON a.accident_index = c.accident_index
    WHERE a.accident_time IS NOT NULL
    GROUP BY EXTRACT(HOUR FROM a.accident_time)
),
by_dow AS (
    SELECT
        d.day_of_week,
        d.day_of_week_name,
        COUNT(*) AS casualties,
        COUNT(CASE WHEN c.severity IN (1, 2) THEN 1 END) AS serious_fatal
    FROM fact_casualty c
    JOIN dim_date d ON d.date_key = c.date_key
    GROUP BY d.day_of_week, d.day_of_week_name
)
SELECT
    'hour_of_day' AS bucket_type,
    hour          AS bucket,
    NULL          AS bucket_name,
    casualties,
    serious_fatal,
    ROUND(100.0 * serious_fatal / NULLIF(casualties, 0), 1) AS pct_serious_fatal
FROM by_hour

UNION ALL

SELECT
    'day_of_week' AS bucket_type,
    day_of_week   AS bucket,
    day_of_week_name AS bucket_name,
    casualties,
    serious_fatal,
    ROUND(100.0 * serious_fatal / NULLIF(casualties, 0), 1) AS pct_serious_fatal
FROM by_dow

ORDER BY bucket_type, bucket;
