# Road Safety Analytics — Data Analyst Project

A third-year CS degree project in a **data analyst** role: turn the raw
DfT **Road Safety Data** (formerly STATS19, Department for Transport) into a
governed SQL data warehouse and an interactive **Power BI** report that answers
real questions for a road-safety authority.

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
│   └── queries/              <- one file per business question (BQ1-BQ8)
├── etl/
│   └── load.py               <- idempotent ETL: CSV -> clean -> warehouse
├── dax/
│   └── measures.dax          <- Power BI DAX measures (KPIs, time intelligence)
└── docs/
    ├── data_quality.md       <- data-quality & governance log
    └── report.md             <- final written report (template)
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
Download `accidents.csv`, `vehicles.csv`, `casualties.csv` from
`https://data.dft.gov.uk/road-accidents-safety-data/` into `data/`.
(See `data/README.md` for details.)

### 4. Install Python deps
```powershell
pip install -r requirements.txt
```

### 5. Run the ETL (idempotent — safe to re-run)
```powershell
python etl/load.py --data-dir data --db-url $DB_URL
```

### 6. Verify
```powershell
psql $DB_URL -c "SELECT COUNT(*) AS accidents FROM fact_accident;"
psql $DB_URL -c "SELECT COUNT(*) AS casualties FROM fact_casualty;"
```

### 7. Power BI
1. Open Power BI Desktop → **Get Data** → **PostgreSQL database**
2. Connect to `road_safety`, load `dim_date`, `dim_location`,
   `fact_accident`, `fact_casualty`, `fact_vehicle`
3. In the model view, set relationships (fact → dim) as single-directional
4. Mark `dim_date` as a **date table** (date column = `full_date`)
5. Paste the measures from `dax/measures.dax` into the relevant tables
6. Build the 4 report pages described in `docs/report.md`

## Business questions answered

See `sql/queries/` — one file per question (BQ1–BQ8). Each file is
self-documenting: the header states the question, assumptions, and how to
read the result.

## Data source & licence

- **Source:** Department for Transport, *Road Safety Data* (formerly STATS19),
  `https://data.dft.gov.uk/road-accidents-safety-data/`
- **Licence:** UK Open Government Licence (OGL v3.0) — cite in your report
- **Data-quality log:** `docs/data_quality.md`

## Status

_Last updated: 2026-10-03._

The project is **mid-Phase 3 (SQL analytics)**. Phases 0–2 are complete and
verified end-to-end; the analytical queries are being validated one by one
against the live warehouse.

| Phase | Scope | Status |
|-------|-------|--------|
| 0 | Environment & toolchain (PostgreSQL 17, Python, psql) | ✅ Complete |
| 1 | Data acquisition & profiling (2025 single-year DfT extract) | ✅ Complete |
| 2 | Star schema + idempotent ETL (3 facts, 2 dimensions) | ✅ Complete & verified |
| 3 | SQL analytics — BQ1–BQ8 | 🔄 In progress (BQ1–BQ6 validated) |
| 4 | Power BI report (model, DAX, 4 pages) | ⏳ Not started |
| 5 | Insights & recommendations | ⏳ Not started |
| 6 | Documentation, testing & presentation | ⏳ Not started |

### Business-question validation (Phase 3)

Each query is run against the live `road_safety` database and cross-checked
for sanity before it is marked validated.

| Query | Question | Status |
|-------|----------|--------|
| BQ1 | Casualty trend over time | ✅ Validated |
| BQ2 | Highest-risk districts / road classes | ✅ Validated (351 real districts) |
| BQ3 | Casualties by weather / lighting / surface | ✅ Validated (all sums exact) |
| BQ4 | Age/sex profile of casualties vs drivers | ✅ Validated (18 bands, no spurious zeros) |
| BQ5 | Vehicle types & manoeuvres in serious/fatal | ✅ Validated (motorcycles dominate) |
| BQ6 | Geographic high-risk clusters | ✅ Validated (urban clusters) |
| BQ7 | Vulnerable road-user (ped/cyclist) share | ⏳ Pending |
| BQ8 | Time-of-day / day-of-week severity patterns | ⏳ Pending |

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

Full detail lives in `docs/data_quality.md` and `docs/report.md`.

Phases 0–6 are defined in
`Plans_data/01_Data_Analyst_Road_Safety_Analytics.txt`.
