# Raw data

This directory holds the three raw DfT "Road Safety Data" CSV files that
the ETL pipeline (`etl/load.py`) reads. The files are **not committed to
git** (see `.gitignore`) because they are large and freely re-downloadable.

## Files

| File | Table | Description |
|------|-------|-------------|
| `accidents.csv` | `fact_accident` + `dim_date` + `dim_location` | One row per recorded road accident. |
| `vehicles.csv` | `fact_vehicle` | One row per vehicle involved in an accident. |
| `casualties.csv` | `fact_casualty` | One row per person injured or killed. |

The three tables are linked by `collision_index`
(accidents 1:N vehicles, 1:N casualties).

## Where to get the data

The classic `data.gov.uk` STATS19 download URLs are **dead (404)**. The
only live source is the DfT Road Safety Data page:

    https://data.dft.gov.uk/road-accidents-safety-data/

From that page you can download:

- **Single year** (used here) — e.g. the 2025 `accidents.csv`,
  `vehicles.csv`, `casualties.csv`.
- **Last 5 years** — `...-collision-last-5-years.csv`, etc.
- **Complete (1979–latest)** — `...-collision-1979-latest-published-year.csv`, etc.

Download the three single-year files and place them in this directory
with the exact names above.

> **Note:** the live source uses a **new column specification** that is
> heavily *coded* (integers) where classic STATS19 was free text. The ETL
> decodes those codes to human-readable labels — see
> `docs/data_quality.md` for the full decision log.

## Licence

UK Open Government Licence (OGL v3.0). You are free to reuse the data,
subject to the licence terms.
