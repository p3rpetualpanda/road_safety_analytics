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

Scaffold complete. Phases 0–6 are defined in
`Plans_data/01_Data_Analyst_Road_Safety_Analytics.txt`.
