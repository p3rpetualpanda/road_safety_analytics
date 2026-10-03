# Data Quality & Governance Log

This log records **every** cleaning decision, assumption, and known
limitation in the pipeline. It is a core deliverable (O4) — a data
analyst is expected to find and document data-quality issues, not just
fix them silently.

> Keep this file current. Add a row each time you change a rule in
> `etl/load.py` or discover a new quirk in the raw data.

## 1. Source

| Item | Value |
|------|-------|
| Dataset | DfT "Road Safety Data" (formerly STATS19) |
| Publisher | Department for Transport |
| Live source | `https://data.dft.gov.uk/road-accidents-safety-data/` |
| Licence | UK Open Government Licence (OGL v3.0) |
| Files | `accidents.csv`, `vehicles.csv`, `casualties.csv` |
| Link key | `collision_index` (accidents 1:N vehicles, 1:N casualties) |
| Year range | 2025 (single-year file loaded) |

> **Note:** the classic `data.gov.uk` STATS19 download URLs are now
> dead (404). The live source is `data.dft.gov.uk`, which publishes a
> **new column specification** that is heavily *coded* (integers) where
> classic STATS19 was free text. The ETL decodes those codes to
> human-readable labels (see decisions 8–14 below).

## 2. Cleaning decisions

| # | Field | Issue found | Decision | Where implemented |
|---|-------|-------------|----------|-------------------|
| 1 | `collision_severity` / `casualty_severity` | Coded 1/2/3, not words | Kept as int; rows outside {1,2,3} dropped & counted | `clean_severity()` |
| 2 | `age_of_casualty` | `-1` / 0 / 99 / 999 = unknown codes | Mapped to NULL; banded as "Unknown" | `clean_age()`, `age_band()` |
| 3 | `time` | New spec is `"HH:MM"` text (legacy was `"HHMM"`) | Parsed to `HH:MM:SS`; invalid → NULL | `clean_time()` |
| 4 | `latitude` / `longitude` | Missing or out of range | Out-of-range → NULL | `clean_coord()` |
| 5 | `casualty_class` | Coded 1/2/3/… (not free text) | VRU flag = class 1 (pedestrian) or 2 (cyclist) | `is_vru()` |
| 6 | Orphaned casualties/vehicles | FK to a dropped accident | Dropped & counted | `run()` |
| 7 | `date` | `DD/MM/YYYY` text | Parsed day-first to a real date | `run()` (dim_date) |
| 8 | `weather_conditions` | Coded 1–9 | Decoded to labels; unmapped → "Unknown" | `decode_code()` |
| 9 | `light_conditions` | Coded 1/4/5/6/7/-1 | Decoded to labels; unmapped → "Unknown" | `decode_code()` |
| 10 | `road_surface_conditions` | Coded 1–5/9/-1 | Decoded to labels; unmapped → "Unknown" | `decode_code()` |
| 11 | `first_road_class` | Coded 1–6/-1 | Decoded to labels; unmapped → "Unknown" | `decode_code()` |
| 12 | `urban_or_rural_area` | Coded 1/2/3 | Decoded to labels; unmapped → "Unknown" | `decode_code()` |
| 13 | `sex_of_casualty` / `sex_of_driver` | Coded 1/2/9/-1 | Decoded to labels; unmapped → "Unknown" | `decode_code()` |
| 14 | `vehicle_type` / `vehicle_manoeuvre` / `propulsion_code` / `age_band_of_driver` | Coded integers | Decoded to labels; unmapped → "Unknown" | `decode_code()` |
| 15 | `speed_limit` | Now lives in the **accidents** table (was casualties) | Moved to `fact_accident.speed_limit` | `run()` |
| 16 | `protection`, `driver_impaired` | **No equivalent** in the new spec | Dropped from the warehouse | `schema.sql` |
| 17 | `local_authority_district` | **100% `-1`** in the 2025 extract (deprecated) — made the district dimension degenerate (all 101,525 accidents → one `-1` row) | Switched the district source to `local_authority_ons_district` (ONS codes: E06=England, E08=Scotland, E09=Wales, S12=Scottish council areas, W06=Wales, E07=London boroughs); `-1` → "Unknown". `dim_location` grew 396 → 2,492 rows. | `run()` (dim_location) |

## 3. Assumptions

- **VRU definition**: casualty class 1 (pedestrian) or 2 (cyclist) is
  treated as a vulnerable road user. Motorists, passengers, and
  motorcyclists are not.
- **Serious+Fatal** = severity 1 (fatal) or 2 (serious). Slight (3)
  is excluded from the headline KPI.
- **Reliability floor**: district/vehicle rankings require a minimum
  accident count (≥ 50 / ≥ 20) to avoid small-sample noise.
- **Geographic clustering** uses a 0.1° grid as a PostGIS-free proxy.
- **Code decoding**: unmapped codes are rendered as "Unknown" rather
  than dropped, so no row is silently lost.

## 4. Known limitations

- The dataset is a **sample** of police-recorded accidents, not a
  census; absolute counts understate true incidence.
- The 2025 file uses the **new coded specification**; several legacy
  columns (`protection`, `driver_impaired`) no longer exist and were
  dropped from the warehouse.
- `local_authority_district` boundaries change over time; historical
  rows may reference defunct districts.
- The 2025 extract's `local_authority_district` is entirely `-1`; we use
  `local_authority_ons_district` (ONS codes) instead. District names are
  **not** in the CSV, so the warehouse stores the ONS code as the label.
  Top-N serious-per-accident rankings are dominated by small Scottish/Welsh
  council areas (ratios 0.5–0.87 vs ~0.29 national) — a real rural-severity
  signal, but volatile at the ≥50-accident floor.
- Time-of-day analysis is limited to records with a valid `time`
  (a minority of rows).
- Some high vehicle/manoeuvre/propulsion codes (e.g. 17–21, 33, 90,
  97, 98, 99) are not in the published code tables and are rendered as
  "Unknown".

## 5. Row-count reconciliation

Fill in after each load (copy from the ETL log):

| Table | Raw rows | Loaded rows | Dropped | Reason |
|-------|----------|-------------|---------|--------|
| accidents | | | | |
| casualties | | | | |
| vehicles | | | | |
| dim_date | | | | |
| dim_location | | | | |

## 6. Change log

| Date | Change | Author |
|------|--------|--------|
| 2026-10-03 | Initial log created | jake |
| 2026-10-03 | Reconciled to the live `data.dft.gov.uk` column spec: new source, coded-field decoding (decisions 8–14), `speed_limit` moved to `fact_accident`, `protection`/`driver_impaired` dropped, `time` now `HH:MM`, unknown-age code `-1` added | jake |
| 2026-10-03 | Discovered `local_authority_district` is 100% `-1` in 2025 (degenerate district dim). Switched district source to `local_authority_ons_district` (ONS codes); re-ran ETL (`dim_location` 396 → 2,492); re-validated BQ2 (351 real districts) | jake |
