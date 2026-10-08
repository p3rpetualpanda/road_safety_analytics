# Road Safety Analytics — Data Analyst Project

A third-year CS degree project in a **data analyst** role: turn the raw
DfT **Road Safety Data** (formerly STATS19, Department for Transport) into a
governed SQL data warehouse and an interactive **Power BI** report that answers
real questions for a road-safety authority. Phase B adds exposure-adjusted
rates using DfT road traffic estimates, vehicle licensing data, and published
casualty rates.

```
raw CSV (data.dft.gov.uk)
   -> SQL warehouse (star schema, cleaned, governed)   [sql/ + etl/]
   -> analytical queries (KPIs, trends, segmentation)  [sql/queries/]
   -> Power BI report (self-service, decision-ready)   [dax/]
   -> insights + recommendations                       [docs/]
```

## Repository layout

```
road_safety_analytics/
├── README.md                 <- you are here
├── requirements.txt          <- Python deps for the ETL
├── Makefile                  <- convenience commands (setup, load, test)
├── .gitignore
├── data/                     <- raw DfT CSVs (gitignored, you add them)
├── sql/
│   ├── schema.sql            <- star schema DDL (3 facts + 2 dimensions)
│   └── queries/              <- one file per business question (BQ1-BQ14)
├── etl/
│   ├── load.py               <- idempotent ETL: CSV -> clean -> warehouse
│   └── load_exposure.py      <- Phase B: ODS exposure data -> warehouse
├── data/
│   ├── exposure/             <- DfT ODS files (TRA, VEH, RAS) for Phase B
│   └── dft_traffic_counts_raw_counts.csv  <- raw traffic counts (optional)
├── dax/
│   ├── measures.dax          <- Power BI DAX measures (21 measures incl. Phase B rates)
│   └── model.tmdl            <- full data model in TMDL (tables, relationships, measures)
└── docs/
    ├── data_quality.md       <- data-quality & governance log
    ├── performance.md        <- EXPLAIN ANALYZE evidence (BQ1, BQ2) + index rationale
    ├── power_bi_guide.md     <- Phase 4 Power BI build guide (connection, model, pages)
    ├── presentation.md       <- 10-15 min presentation deck (markdown slides)
    └── report.md             <- final written report
```

## Prerequisites

- **PostgreSQL 14+** (or SQL Server — but this scaffold targets PostgreSQL)
- **Python 3.10+**
- **Power BI Desktop** (free)
- The three DfT CSVs from the *Road Safety Data* page on
  `https://data.dft.gov.uk/road-accidents-safety-data/`

## How to run (target: < 30 minutes from a clean state)

### 1. Create the database
```powershell
createdb road_safety
```

### 2. Apply the schema
```powershell
$DB_URL = "postgresql://postgres:postgres@localhost:5432/road_safety"
psql $DB_URL -f sql/schema.sql
```

### 3. Add the raw data
Download the 5-year extracts from DfT into `data/`:
- `https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-collision-last-5-years.csv` → `accidents.csv`
- `https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-vehicle-last-5-years.csv` → `vehicles.csv`
- `https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-casualty-last-5-years.csv` → `casualties.csv`
(See `data/README.md` for details.)

### 4. Install Python deps
```powershell
pip install -r requirements.txt
```

### 5. Run the ETL (idempotent — safe to re-run)
```powershell
python etl/load.py --data-dir data --db-url $DB_URL
```

### 6. Run the exposure ETL (Phase B — optional)
```powershell
python etl/load_exposure.py --data-dir data/exposure --db-url $DB_URL
```

### 7. Verify
```powershell
psql $DB_URL -c "SELECT COUNT(*) AS accidents FROM fact_accident;"
psql $DB_URL -c "SELECT COUNT(*) AS casualties FROM fact_casualty;"
psql $DB_URL -c "SELECT COUNT(*) AS exposure_rows FROM exposure_vehicle_km;"
```

### 8. Power BI
Full step-by-step build guide: **[`docs/power_bi_guide.md`](docs/power_bi_guide.md)**.
1. Open Power BI Desktop → **Get Data** → **PostgreSQL database**
2. Connect to `road_safety`, load `dim_date`, `dim_location`,
   `fact_accident`, `fact_casualty`, `fact_vehicle`,
   `exposure_vehicle_km`, `exposure_licensed_vehicles`,
   `ras0201_numbers`, `ras0201_rates`, `ras4001_cost_per_casualty`, `ras4001_total_cost`
3. In the model view, set the 5 single-directional relationships (see guide §2)
4. Mark `dim_date` as a **date table** (date column = `full_date`)
5. Add the measures from `dax/measures.dax` (21 measures)
6. Build the 5 report pages described in the guide §5

## Business questions answered

See `sql/queries/` — one file per question (BQ1–BQ14). Each file is
self-documenting: the header states the question, assumptions, and how to
read the result. BQ12–BQ14 (Phase B) use exposure-adjusted rates.

## Data source & licence

- **Source:** Department for Transport, *Road Safety Data* (formerly STATS19),
  `https://data.dft.gov.uk/road-accidents-safety-data/`
- **Licence:** UK Open Government Licence (OGL v3.0) — cite in your report
- **Data-quality log:** `docs/data_quality.md`
- **Performance analysis:** `docs/performance.md` (EXPLAIN evidence)
- **Presentation:** `docs/presentation.md` (10-15 min deck)

## Status

_Last updated: 2026-10-07._

The project is **complete (Phases 0–6 + Phase A + Phase B)**. All 14 business
questions are validated against the live warehouse, the Power BI report
(`road_safety_visuals.pbix`) is built with all 5 pages, the star schema, and
21 DAX measures, the final written report (`docs/report.md`) is finished
with evidence-based insights and recommendations, query performance is
documented with `EXPLAIN ANALYZE` evidence (`docs/performance.md`), and the
10-15 minute presentation deck is ready (`docs/presentation.md`).

| Phase | Scope | Status |
|-------|-------|--------|
| 0 | Environment & toolchain (PostgreSQL 17, Python, psql) | ✅ Complete |
| 1 | Data acquisition & profiling (2021–2025 five-year DfT extract) | ✅ Complete |
| 2 | Star schema + idempotent ETL (3 facts, 2 dimensions) | ✅ Complete & verified |
| 3 | SQL analytics — BQ1–BQ14 | ✅ Complete (all 14 validated) |
| 4 | Power BI report (model, DAX, 5 pages) | ✅ Complete (report built, 21 measures) |
| 5 | Insights & recommendations | ✅ Complete (8 insights in `docs/report.md`) |
| 6 | Documentation, testing & presentation | ✅ Complete (36 tests passing, report finalised, `docs/performance.md`, `docs/presentation.md`) |
| A | Multi-year expansion (2021–2025) | ✅ Complete (5-year ETL, BQ9–BQ11, 3 new DAX measures) |
| B | Exposure-adjusted rates (TRA, VEH, RAS) | ✅ Complete (exposure ETL, BQ12–BQ14, 5 new DAX measures) |

### Business-question validation (Phase 3)

Each query is run against the live `road_safety` database and cross-checked
for sanity before it is marked validated.

| Query | Question | Status |
|-------|----------|--------|
| BQ1 | Casualty trend over time | ✅ Validated (5-year monthly trend) |
| BQ2 | Highest-risk districts / road classes | ✅ Validated (375 real districts) |
| BQ3 | Casualties by weather / lighting / surface | ✅ Validated (all sums exact) |
| BQ4 | Age/sex profile of casualties vs drivers | ✅ Validated (18 bands, no spurious zeros) |
| BQ5 | Vehicle types & manoeuvres in serious/fatal | ✅ Validated (motorcycles dominate) |
| BQ6 | Geographic high-risk clusters | ✅ Validated (urban clusters) |
| BQ7 | Vulnerable road-user (ped/cyclist) share | ✅ Validated (35.5% VRU, ~57.2% broad vulnerable) |
| BQ8 | Time-of-day / day-of-week severity patterns | ✅ Validated (all sums exact) |
| BQ9 | Annual trend & year-on-year change | ✅ Validated (S/F share rising 19.4%→22.9%) |
| BQ10 | Seasonality index | ✅ Validated (Feb lowest 81.2, Jun highest 109.0) |
| BQ11 | Inflection points & anomalies | ✅ Validated (recurring Feb dips, Jun/Jul spikes) |
| BQ12 | S/F rate per 100M km by road class | ✅ Validated (motorway 25.69, minor urban 7.34) |
| BQ13 | S/F rate per 100K licensed vehicles | ✅ Validated (61.9→69.3, +12.0% over 5 years) |
| BQ14 | S/F rate per 100M km by local authority | ✅ Validated (186 LAs, Inner London top) |

### Notable data findings so far

- **2025 `local_authority_district` is 100% `-1`** (unknown). District
  attribution therefore uses `local_authority_ons_district` (ONS codes),
  which resolved `dim_location` from 396 → 2,492 rows and restored real
  district-level analysis for BQ2/BQ6.
- **BQ4 age-band defect fixed** — casualties and drivers are now mapped onto a
  common reporting grid (18 bands) so the two populations are directly
  comparable with no artificial zero rows.
- **BQ5 signal:** motorcycles are disproportionately represented in
  serious/fatal casualties relative to their share of traffic.
- **BQ7 signal:** ~57.2% of serious/fatal casualties are vulnerable road users
  (car occupants 37.7% + VRUs 35.5% + motorcyclists 19.6%). The VRU share is
  stable across the five years (34.6–36.0%).
- **BQ8 signal:** severity share peaks on Sundays (23.1%) and in the small
  hours (3am 27.9%), versus 8am (17.0%).
- **BQ9 signal:** serious/fatal share is rising every year — from 19.4% in 2021
  to 22.9% in 2025, with a +6.0% YoY jump in 2025 (partly driven by the
  September 2026 DfT coding revision for e-scooters/PPTs).
- **BQ13 signal (Phase B):** per-vehicle risk is rising — S/F per 100K licensed
  vehicles increased 12.0% from 61.9 (2021) to 69.3 (2025). The rise in
  serious/fatal casualties is not simply a function of fleet growth.
- **BQ12 signal (Phase B):** motorways have the highest S/F rate per 100M km
  (25.69) vs minor urban roads (7.34), reflecting higher speeds and severity.
- **BQ14 signal (Phase B):** Inner London boroughs have the highest
  exposure-adjusted S/F rates (17–45 per 100M km), reflecting urban density
  and VRU exposure.

Full detail lives in `docs/data_quality.md` and `docs/report.md`.

Phases 0–6 are defined in
`Plans_data/01_Data_Analyst_Road_Safety_Analytics.txt`.
