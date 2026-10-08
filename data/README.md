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
live source is the DfT Road Safety Data page:

    https://www.gov.uk/government/statistics/road-safety-data

This project uses the **last-5-years** extract (2021–2025), downloaded
directly from the DfT data service:

- `https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-collision-last-5-years.csv`
- `https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-vehicle-last-5-years.csv`
- `https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-casualty-last-5-years.csv`

Rename each file to `accidents.csv`, `vehicles.csv`, `casualties.csv`
respectively and place them in this directory.

Other available extracts (not used here):

- **Single year** — e.g. the 2025 `...-collision-2025.csv`, etc.
- **Complete (1979–latest)** — `...-collision-1979-latest-published-year.csv`, etc.

> **Note:** the live source uses a **new column specification** that is
> heavily *coded* (integers) where classic STATS19 was free text. The ETL
> decodes those codes to human-readable labels — see
> `docs/data_quality.md` for the full decision log.

## `data/exposure/` — Phase B exposure data (DfT national statistics)

Ten ODS (OpenDocument Spreadsheet) files downloaded from the DfT Road Safety
Data page. These are **committed to git** (small, ~1.2 MB total) because they
are the authoritative source for the exposure-adjusted rate measures.

| File | DfT source | Description |
|------|-----------|-------------|
| `ras0201_numbers_and_rates.ods` | RAS0201 | KSI counts and rates by road user type and severity. |
| `ras4001_cost_of_prevention.ods` | RAS4001 | Cost of road casualties (per-casualty and total, by collision year and price year). |
| `tra0201_km_by_vehicle_type.ods` | TRA0201 | Vehicle-km by vehicle type (national). |
| `tra0202_km_by_road_class.ods` | TRA0202 | Vehicle-km by road class (national). |
| `tra0204_km_by_vehicle_and_road_type.ods` | TRA0204 | Vehicle-km by vehicle type and road type. |
| `tra0401_pedal_cycle_traffic.ods` | TRA0401 | Pedal cycle traffic volumes. |
| `tra0412_pedal_cycle_by_road_class.ods` | TRA0412 | Pedal cycle traffic by road class. |
| `tra8904_km_by_local_authority.ods` | TRA8904 | Vehicle-km by local authority. |
| `tra8905_km_by_la_and_vehicle_type.ods` | TRA8905 | Vehicle-km by local authority and vehicle type. |
| `veh0101_licensed_vehicles.ods` | VEH0101 | Licensed vehicles by type (national). |

Loaded by `etl/load_exposure.py` into six warehouse tables:
`exposure_vehicle_km`, `exposure_licensed_vehicles`, `ras0201_numbers`,
`ras0201_rates`, `ras4001_cost_per_casualty`, `ras4001_total_cost`.

## Licence

UK Open Government Licence (OGL v3.0). You are free to reuse the data,
subject to the licence terms.
