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
| Year range | 2021–2025 (last-5-years extract) |

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
| 5 | `casualty_class` / `casualty_type` | Two distinct coded fields conflated in the old spec | `casualty_class` = **role** (1=Driver/rider, 2=Passenger, 3=Pedestrian); `casualty_type` = **road-user type** (0=Pedestrian, 1=Cyclist, 9=Car occupant, …). VRU flag now = `casualty_type` in {0, 1} | `is_vru()`, `decode_code()` |
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

## 3. Code-Stability Audit (2021–2025)

Before loading the 5-year extract, every coded column was audited against
the DfT **Road Safety Open Dataset Data Guide** (2025 edition) to confirm
that the code→label mappings in `etl/load.py` match the authoritative
scheme. The audit compared the distinct codes present in the raw CSVs
against the `2024_code_list` sheet of the data guide.

**Data guide source:**
`https://assets.publishing.service.gov.uk/media/6ab2a71d997a4b2950cced58/dft-road-casualty-statistics-road-safety-open-dataset-data-guide-2025.xlsx`

### 3.1 Unmapped codes found (7)

| Column | Code | Rows | Resolution |
|--------|------|------|------------|
| `weather_conditions` | `-1` | 12 | Added `-1: "Unknown"` to `WEATHER_CONDITIONS` |
| `road_surface_conditions` | `-1` | 3,527 | Added `-1: "Unknown"` to `ROAD_SURFACE_CONDITIONS` |
| `vehicle_type` | `-1` | 661 | Added `-1: "Unknown"` to `VEHICLE_TYPE` |
| `vehicle_type` | `22` | 1,628 | Added `22: "Mobility scooter"` (data guide) |
| `vehicle_type` | `23` | 1,902 | Added `23: "Electric motorcycle"` (data guide) |
| `vehicle_manoeuvre` | `20` | 582 | Added `20: "Parking"` (data guide) |
| `propulsion_code` | `11` | 3 | Added `11: "Fuel cells"` (data guide) |

All 7 codes are now mapped. No unmapped codes remain.

### 3.2 Scheme corrections

Several mapping dictionaries in `etl/load.py` were using the **wrong
code scheme** (labels from the legacy STATS19 spec rather than the
current DfT data guide). The audit identified and corrected:

| Dictionary | Old scheme (wrong) | New scheme (data guide) |
|------------|--------------------|-------------------------|
| `VEHICLE_TYPE` | Legacy STATS19 labels (e.g. 9="Car" was correct, but 22/23 missing) | Data guide 2024 labels (22="Mobility scooter", 23="Electric motorcycle", 33="Personal powered transporter (e-scooter)") |
| `VEHICLE_MANOEUVRE` | Legacy labels (e.g. 20 missing) | Data guide 2024 labels (20="Parking") |
| `AGE_BAND_OF_DRIVER` | Old 5-year bands (1="17-20", 2="21-30", …) | Data guide bands (1="0-5", 2="6-10", …, 11="Over 75") |
| `PROPULSION_CODE` | Internal conflict (codes 5 AND 8 both = "Hybrid") | Data guide legacy fuel scheme (1="Petrol", 2="Heavy oil (diesel)", 3="Electric", …, 11="Fuel cells", 12="Electric diesel") |

**`propulsion_code` decision:** The data guide `2024_code_list` sheet
shows the **legacy fuel scheme** (1=Petrol, 2=Heavy oil, 3=Electric,
4=Steam, 5=Gas, 6=Petrol/Gas (LPG), 7=Gas/Bi-fuel, 8=Hybrid electric,
9=Gas Diesel, 10=New fuel technology, 11=Fuel cells, 12=Electric
diesel). The old `load.py` scheme had an internal conflict (codes 5 and
8 both mapped to "Hybrid"), proving it was wrong. Code 2 is labelled
"Heavy oil (diesel)" since UK road-vehicle practice uses heavy oil as
the diesel designation. Actual data distribution confirms plausibility:
1=379K (Petrol), 2=272K (Diesel), 3=16K (Electric), 8=47K (Hybrid).

### 3.3 `casualty_class` vs `casualty_type` architectural decision

The 5-year extract uses **two distinct coded fields** that the old
single-year spec conflated:

- **`casualty_class`** (role): 1=Driver or rider, 2=Passenger,
  3=Pedestrian. This is the *role* the person played in the accident.
- **`casualty_type`** (road-user type): 0=Pedestrian, 1=Cyclist,
  2=Motorcycle ≤50cc, …, 9=Car occupant, …, 33=Personal powered
  transporter (e-scooter), 90=Other vehicle occupant, 97=Motorcycle
  unknown cc, 98=Goods vehicle unknown weight, 99=Unknown vehicle type
  (self reported), -1=Unknown. This is the *type of road user* the
  person was.

**Cross-tab verification (5-year data):**
- `casualty_class=3` (Pedestrian) → 100% `casualty_type=0` (94,398 rows)
- `casualty_class=1` (Driver/rider) → various `casualty_type` values
- `casualty_class=2` (Passenger) → various `casualty_type` values

**Decision:** Both fields are now stored in `fact_casualty` as separate
columns. `vru_flag` is derived from `casualty_type` (0=Pedestrian or
1=Cyclist), not from `casualty_class`. This is more accurate because a
pedestrian's `casualty_class` is 3, but a cyclist's `casualty_class`
is 1 (Driver/rider) — the old VRU definition (class 1 or 2) would have
incorrectly flagged all drivers/riders as VRUs.

### 3.4 `casualty_type` code 33 (e-scooter)

Code 33 ("Personal powered transporter (e-scooter)") is present in the
5-year data (5,719 rows) but was **not in the data guide's
`2024_code_list`** sheet. It was added per the **September 2026 DfT
revision note**:

> "The coding of vehicle type (within the vehicles extract) and road
> user type (within the casualty extract) has been improved to
> separately identify 'powered personal transporters' (including
> e-scooters) which were previously included within the 'other'
> category. An additional flag to identify e-scooter casualties has
> been added to the casualty data extract."

The `escooter_flag` column in `casualties.csv` is not yet used in the
warehouse (no corresponding column in `fact_casualty`); it may be added
in a future phase.

### 3.5 VRU definition change

**Old definition (single-year 2025 data):** `casualty_class` in {1, 2}
(pedestrian or cyclist).

**New definition (5-year 2021–2025 data):** `casualty_type` in {0, 1}
(pedestrian or cyclist).

This is a **semantic correction**, not just a code remapping. The old
definition was wrong because `casualty_class=1` means "Driver or rider"
(not "Pedestrian"), so the old VRU flag would have flagged all
drivers/riders as VRUs. The new definition correctly identifies
pedestrians and cyclists by their road-user type.

## 4. Assumptions

- **VRU definition**: `casualty_type` 0 (pedestrian) or 1 (cyclist) is
  treated as a vulnerable road user. Motorists, passengers, and
  motorcyclists are not. (Corrected from the old `casualty_class`
  definition — see §3.5.)
- **Serious+Fatal** = severity 1 (fatal) or 2 (serious). Slight (3)
  is excluded from the headline KPI.
- **Reliability floor**: district/vehicle rankings require a minimum
  accident count (≥ 50 / ≥ 20) to avoid small-sample noise.
- **Geographic clustering** uses a 0.1° grid as a PostGIS-free proxy.
- **Code decoding**: unmapped codes are rendered as "Unknown" rather
  than dropped, so no row is silently lost.

## 5. Known limitations

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
- `casualty_type` code 33 ("Personal powered transporter (e-scooter)")
  is present in the data but was not in the data guide's `2024_code_list`
  sheet; it was added per the September 2026 DfT revision note (see §3.4).
- **Large "Unknown" buckets in `vehicle_type` and `manoeuvre`.** In the
  2025 extract, ~67% of vehicle records have `vehicle_type = "Unknown"` and
  ~61.6% have `manoeuvre = "Unknown"`. This is a genuine source-data gap
  (the new coded spec leaves these fields blank or uses unmapped codes for a
  large share of records), not an ETL bug — the values are verified against
  the live warehouse. Any vehicle-type or manoeuvre analysis should treat
  the "Unknown" bar as a real, dominant category and be read with that
  caveat; it is not a rendering artefact.

## 6. Row-count reconciliation

Verified against the live warehouse on 2026-10-07 (after the final 5-year
ETL run):

| Table | Raw rows | Loaded rows | Dropped | Reason |
|-------|----------|-------------|---------|--------|
| accidents | 513,801 | 513,801 | 0 | — |
| casualties | 652,821 | 652,821 | 0 | — |
| vehicles | 937,265 | 937,265 | 0 | — |
| dim_date | — | 1,826 | — | Derived (one row per day, 2021–2025) |
| dim_location | — | 2,901 | — | Derived (distinct ONS district codes) |

Accidents by year (loaded): 2021 = 101,087; 2022 = 106,004;
2023 = 104,258; 2024 = 100,927; 2025 = 101,525.

The warehouse is a faithful 1:1 load of the raw CSVs — no rows were
dropped by cleaning rules in the 2021–2025 extract (all severity codes
were valid, no orphaned casualties/vehicles, all dates parsed). The
`vru_flag` column is populated from the raw numeric `casualty_type`
(0 = pedestrian, 1 = cyclist) before it is decoded to text labels;
172,139 of 652,821 casualties are flagged VRU (94,398 pedestrians +
77,741 cyclists).

## 7. Change log

| Date | Change | Author |
|------|--------|--------|
| 2026-10-07 | Loaded the full 2021–2025 extract (513,801 accidents / 652,821 casualties / 937,265 vehicles; `dim_date` 1,826, `dim_location` 2,901). Fixed a `vru_flag` ordering bug: the flag was computed after `casualty_type` was decoded to text, so `to_numeric()` coerced every label to NaN and the flag was always False — now derived from the raw numeric column first (172,139 True). Added a `collision_index` uniqueness + referential-integrity assertion to the ETL | jake |
| 2026-10-06 | Code-stability audit of the 2021–2025 extract against the DfT data guide (2025): 7 unmapped codes added (weather/road_surface `-1`, vehicle_type `-1`/22/23, manoeuvre 20, propulsion 11); `VEHICLE_TYPE`, `VEHICLE_MANOEUVRE`, `AGE_BAND_OF_DRIVER`, `PROPULSION_CODE` dicts corrected to the data-guide scheme; `casualty_class` (role) split from `casualty_type` (road-user type) — new `casualty_class` column in `fact_casualty`; VRU flag redefined as `casualty_type` in {0,1}; BQ4 driver-age CASE rewritten to the new band scheme | jake |
| 2026-10-03 | Initial log created | jake |
| 2026-10-03 | Reconciled to the live `data.dft.gov.uk` column spec: new source, coded-field decoding (decisions 8–14), `speed_limit` moved to `fact_accident`, `protection`/`driver_impaired` dropped, `time` now `HH:MM`, unknown-age code `-1` added | jake |
| 2026-10-03 | Discovered `local_authority_district` is 100% `-1` in 2025 (degenerate district dim). Switched district source to `local_authority_ons_district` (ONS codes); re-ran ETL (`dim_location` 396 → 2,492); re-validated BQ2 (351 real districts) | jake |
| 2026-10-04 | Documented the large "Unknown" buckets in `vehicle_type` (~67%) and `manoeuvre` (~61.6%) as a genuine 2025-extract source-data gap (verified against the live warehouse), not an ETL bug | jake |
