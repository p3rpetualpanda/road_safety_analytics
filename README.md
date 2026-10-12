# Road Safety Analytics — Data Analyst Project

![CI](https://github.com/p3rpetualpanda/road_safety_analytics/actions/workflows/ci.yml/badge.svg)

A final-year CS degree project in a **data analyst** role: turn the raw
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
├── requirements-dev.txt      <- dev deps (pytest, ruff)
├── Makefile                  <- convenience commands (setup, load, test, lint, check)
├── ruff.toml                 <- lint configuration
├── .gitignore
├── .github/
│   └── workflows/ci.yml      <- CI: lint + unit tests on every push/PR
├── data/
│   ├── README.md             <- where to get the raw CSVs + exposure files
│   ├── exposure/             <- DfT ODS files (TRA, VEH, RAS) for Phase B (committed)
│   └── *.csv                 <- raw DfT CSVs (gitignored, you add them)
├── sql/
│   ├── schema.sql            <- star schema DDL (3 facts + 2 dimensions)
│   └── queries/              <- one file per business question (BQ1-BQ14)
├── etl/
│   ├── load.py               <- idempotent ETL: CSV -> clean -> warehouse
│   └── load_exposure.py      <- Phase B: ODS exposure data -> warehouse
├── tests/
│   ├── conftest.py           <- path setup + DB-driver stub (tests run without a DB)
│   ├── test_cleaning.py      <- 36 tests for the cleaning/transform layer
│   └── test_exposure_helpers.py  <- 20 tests for the Phase B parsing helpers
├── dax/
│   ├── measures.dax          <- Power BI DAX measures (21 measures incl. Phase B rates)
│   └── model.tmdl            <- full data model in TMDL (11 tables, 8 relationships, measures)
└── docs/
    ├── data_quality.md       <- data-quality & governance log
    ├── performance.md        <- EXPLAIN ANALYZE evidence (BQ1, BQ2) + index rationale
    ├── power_bi_guide.md     <- Phase 4 Power BI build guide (local-only, not tracked)
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
3. In the model view, set the 8 single-directional relationships (see guide §2)
4. Mark `dim_date` as a **date table** (date column = `full_date`)
5. Add the measures from `dax/measures.dax` (21 measures)
6. Build the 5 report pages described in the guide §5

## Business questions answered

See `sql/queries/` — one file per question (BQ1–BQ14). Each file is
self-documenting: the header states the question, assumptions, and how to
read the result. BQ12–BQ14 (Phase B) use exposure-adjusted rates.

## Testing & CI

The cleaning/transform layer — where every data-quality decision lives — is
unit-tested in isolation (no database required: `tests/conftest.py` stubs the
DB driver, so the suite runs anywhere pandas does):

```powershell
make test                 # or: python -m pytest tests/ -q
```

- **56 tests** — `tests/test_cleaning.py` covers severity, age bands, time
  parsing (new + legacy spec), coordinates, VRU flagging, code decoding and
  row serialisation; `tests/test_exposure_helpers.py` covers the Phase B ODS
  parsing helpers (year detection, unit conversion, melt orientations).
- **CI** runs the same suite plus `ruff` on every push/PR
  (`.github/workflows/ci.yml`). One command locally: `make check`.

## Skills demonstrated

| Skill | Where to see it |
|-------|-----------------|
| Data engineering (ETL) | `etl/load.py`, `etl/load_exposure.py` — idempotent, transactional, fully logged |
| Data modelling | `sql/schema.sql` — star schema, 3 facts + 2 dimensions + 6 exposure tables |
| SQL analytics | `sql/queries/` — 14 business questions (CTEs, window functions, ranking) |
| Data quality & governance | `docs/data_quality.md` — decision log, code-stability audit, OGL citation |
| Performance engineering | `docs/performance.md` — EXPLAIN ANALYZE, index design, work_mem tuning |
| DAX / Power BI | `dax/measures.dax`, `dax/model.tmdl` — 21 measures, 11-table versionable TMDL model |
| Testing & CI | `tests/` (56 tests), `make check`, GitHub Actions workflow |
| Documentation | `docs/report.md`, `docs/presentation.md`, this README |

## Data source & licence

- **Source:** Department for Transport, *Road Safety Data* (formerly STATS19),
  `https://data.dft.gov.uk/road-accidents-safety-data/`
- **Licence:** UK Open Government Licence (OGL v3.0) — cite in your report
- **Data-quality log:** `docs/data_quality.md`
- **Performance analysis:** `docs/performance.md` (EXPLAIN evidence)
- **Presentation:** `docs/presentation.md` (10-15 min deck)

## Status

_Last updated: 2026-10-12._

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
| 6 | Documentation, testing & presentation | ✅ Complete (56 tests passing, CI on every push/PR, report finalised, `docs/performance.md`, `docs/presentation.md`) |
| A | Multi-year expansion (2021–2025) | ✅ Complete (5-year ETL, BQ9–BQ11, 3 new DAX measures) |
| B | Exposure-adjusted rates (TRA, VEH, RAS) | ✅ Complete (exposure ETL, BQ12–BQ14, 5 new DAX measures) |

### Business-question validation (Phase 3)

Each query is run against the live `road_safety` database and cross-checked
for sanity before it is marked validated.

| Query | Question | Status |
|-------|----------|--------|
| BQ1 | Casualty trend over time | ✅ Validated (5-year monthly trend) |
| BQ2 | Highest-risk districts / road classes | ✅ Validated (370 real districts) |
| BQ3 | Casualties by weather / lighting / surface | ✅ Corrected 2026-10-12 (code tables fixed; weather barely affects severity) |
| BQ4 | Age/sex profile of casualties vs drivers | ✅ Corrected 2026-10-12 (bands aligned to DfT driver bands) |
| BQ5 | Vehicle types & manoeuvres in serious/fatal | ✅ Validated (motorcycles dominate) |
| BQ6 | Geographic high-risk clusters | ✅ Corrected 2026-10-12 (per-collision coordinates; top 5 cells in London) |
| BQ7 | Vulnerable road-user (ped/cyclist) share | ✅ Validated (35.5% VRU, ~57.2% broad vulnerable) |
| BQ8 | Time-of-day / day-of-week severity patterns | ✅ Validated (all sums exact) |
| BQ9 | Annual trend & year-on-year change | ✅ Validated (S/F share rising 19.4%→22.9%) |
| BQ10 | Seasonality index | ✅ Corrected 2026-10-12 (S/F index: Feb lowest 77.6, Jul highest 111.0) |
| BQ11 | Inflection points & anomalies | ✅ Validated (Feb dips every year; summer spikes vary) |
| BQ12 | S/F rate per 100M km by road class | ✅ Corrected 2026-10-12 (minor urban 9.11 highest, motorway 0.77 lowest) |
| BQ13 | S/F rate per 100K licensed vehicles | ✅ Corrected 2026-10-12 (GB fleet: 63.8→71.5, +12.1%) |
| BQ14 | S/F rate per 100M km by local authority | ✅ Validated (186 LAs, Inner London top) |

### Notable data findings so far

- **2025 `local_authority_district` is 100% `-1`** (unknown). District
  attribution therefore uses `local_authority_ons_district` (ONS codes),
  which resolved `dim_location` from 396 → 2,492 rows and restored real
  district-level analysis for BQ2/BQ6.
- **BQ4 age bands aligned** — casualties and drivers are mapped onto a grid
  whose edges match the DfT driver bands (0-15, 16-25, 26-35, 36-45, 46+), so
  the two populations are directly comparable. 16-25s are over-represented
  among casualties relative to drivers.
- **BQ5 signal:** motorcycles are disproportionately represented in
  serious/fatal casualties relative to their share of traffic.
- **BQ7 signal:** ~57.2% of serious/fatal casualties are vulnerable road users
  (VRUs 35.5% + motorcyclists 19.7% + e-scooter/e-motorcycle users 2.1%; car
  occupants are the largest single group at 37.7%). The VRU share is
  stable across the five years (34.6–36.0%).
- **BQ8 signal:** severity share peaks on Sundays (23.1%) and in the small
  hours (3am 27.9%), versus 8am (17.0%).
- **BQ9 signal:** serious/fatal share is rising every year — from 19.4% in 2021
  to 22.9% in 2025, with a +6.0% YoY jump in 2025. It still rises on DfT's
  adjusted severity (20.6% → 23.4%), so it is not only a recording change.
- **BQ13 signal (Phase B):** per-vehicle risk is rising — S/F per 100K licensed
  vehicles (GB) increased 12.1% from 63.8 (2021) to 71.5 (2025). The rise in
  serious/fatal casualties is not simply a function of fleet growth.
- **BQ12 signal (Phase B):** urban roads have the highest S/F rate per 100M km
  (minor urban 9.11, urban 'A' 8.71); motorways are the safest per km (0.77).
- **BQ14 signal (Phase B):** Inner London boroughs have the highest
  exposure-adjusted S/F rates (17–45 per 100M km), reflecting urban density
  and VRU exposure.

Full detail lives in `docs/data_quality.md` and `docs/report.md`.

Phases 0–6 are defined in the project plan
`01_Data_Analyst_Road_Safety_Analytics.txt` (kept local, gitignored).
