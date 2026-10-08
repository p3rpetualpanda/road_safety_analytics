# Query Performance Analysis

Evidence for the "Performance: basic indexing, EXPLAIN on at least one query"
item in the SQL skills matrix. All plans were captured with
`EXPLAIN (ANALYZE, BUFFERS)` against the live `road_safety` warehouse
(513,801 accidents / 652,821 casualties / 937,265 vehicles, 5-year extract 2021–2025)
on 2026-10-06.

## 1. Indexes

`sql/schema.sql` defines 9 B-tree indexes on the join and filter columns of
the fact tables:

| Index | Table | Column(s) | Serves |
|-------|-------|-----------|--------|
| `idx_fact_accident_date` | `fact_accident` | `date_key` | BQ1, BQ8 (time joins/filters) |
| `idx_fact_accident_location` | `fact_accident` | `location_key` | BQ2, BQ6 (location joins) |
| `idx_fact_accident_severity` | `fact_accident` | `severity` | BQ1, BQ7 (severity filters) |
| `idx_fact_casualty_date` | `fact_casualty` | `date_key` | BQ1, BQ4, BQ8 |
| `idx_fact_casualty_location` | `fact_casualty` | `location_key` | BQ2, BQ6 |
| `idx_fact_casualty_severity` | `fact_casualty` | `severity` | BQ1, BQ4, BQ7 |
| `idx_fact_casualty_vru` | `fact_casualty` | `vru_flag` | BQ7 (VRU share) |
| `idx_fact_vehicle_accident` | `fact_vehicle` | `accident_index` | BQ5 (vehicle joins) |
| `idx_fact_vehicle_type` | `fact_vehicle` | `vehicle_type` | BQ5 (vehicle type filters) |

## 2. BQ2 — heaviest query (district serious-injury rates)

Full plan (abridged to the interesting nodes):

```
Sort  (actual time=5290.586..5290.599 rows=375 loops=1)
  ->  Append
        ->  Subquery Scan on district_stats
              ->  WindowAgg  (RANK() OVER ...)
                    ->  Sort  (quicksort, Memory: 51kB)
                          ->  GroupAggregate  (Group Key: l.district)
                                Filter: count(DISTINCT accident_index) >= 50
                                ->  Sort  (Sort Key: l.district, a.accident_index)
                                      Sort Method: external merge  Disk: 33232kB   <-- spill
                                      ->  Hash Join  (a.location_key = l.location_key)
                                            ->  Hash Right Join  (c.accident_index = a.accident_index)
                                                  ->  Seq Scan on fact_casualty   (652,821 rows, 20.3 ms)
                                                  ->  Hash  (513,801 rows, Memory: 4269kB)
                                                        ->  Seq Scan on fact_accident (513,801 rows, 33.5 ms)
                                            ->  Hash  (2,901 rows, Memory: 168kB)
                                                  ->  Seq Scan on dim_location
        ->  Subquery Scan on road_class_stats  (similar shape, Disk: 39088kB spill)
Planning Time: 4.349 ms
Execution Time: 5304.608 ms
```

### Reading the plan

- **Hash joins, not nested loops** — correct choice: both fact tables are
  scanned in full (100% of rows qualify), so a hash join with a small
  build side (`dim_location`, 2,901 rows → 168 kB hash) is optimal.
- **Sequential scans on the facts** — also correct: the query aggregates
  the *entire* table, so an index scan would add random I/O for no
  selectivity gain. The indexes in §1 matter for *filtered* queries
  (e.g. "accidents in district X in March"), not for full-table
  aggregates.
- **The one inefficiency: `external merge Disk: 33232kB`** — the
  `GROUP BY` sort (652,821 rows) exceeded the default `work_mem`
  (4 MB) and spilled to disk. The road-class branch spills even more
  (39,088 kB). This is a server setting, not a query defect.

### Tuning demonstration

Re-running the identical query with `SET work_mem = '64MB'`:

| Run | Group-by sort | Execution time |
|-----|---------------|----------------|
| default `work_mem` (4 MB) | external merge, **Disk: 33232 kB** | **5,305 ms** |
| `work_mem = 64MB` | quicksort, **Memory: 58675 kB** | **4,613 ms** |

The spill disappears and the query is ~13% faster. On a production
server (or a larger `work_mem`), BQ2-class queries run entirely in
memory.

## 3. BQ1 — light query (monthly casualty trend)

```
Sort  (quicksort, Memory: 32kB)
  ->  Hash Join  (c.date_key = d.date_key)
        ->  Parallel Seq Scan on fact_casualty   (2 workers, 217,607 rows each)
        ->  Seq Scan on dim_date                 (1,826 rows, Memory: 111kB)
Planning Time: 1.015 ms
Execution Time: 81.785 ms
```

Postgres automatically **parallelised** the scan (2 workers), and the
tiny `dim_date` hash build makes the join nearly free. 82 ms end-to-end.

## 4. Conclusions

1. The planner is making sound choices: hash joins for full-table
   aggregates, parallel scans where beneficial, in-memory sorts where
   they fit.
2. The only observed inefficiency (disk-spilled group-by sort) is a
   `work_mem` configuration issue, demonstrated and resolved in §2.
3. All 14 business queries complete in 82 ms – 5,305 ms on the
   5-year extract, which is comfortably within interactive Power BI
   refresh limits.
4. The 9 indexes target the filtered-query and join patterns that will
   dominate as the warehouse grows further (the classic
   STATS19 archive is ~40 years / ~3.5 M accidents), where sequential
   scans stop being free.
