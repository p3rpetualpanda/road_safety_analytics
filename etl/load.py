"""
Road Safety Analytics — ETL pipeline
====================================
Reads the three raw DfT "Road Safety Data" CSVs (accidents, vehicles,
casualties) from data.dft.gov.uk, cleans/transforms them, and loads
them into the PostgreSQL star schema defined in sql/schema.sql.

Design goals
------------
- Idempotent: TRUNCATE + reload, so it can be re-run safely.
- Documented: every cleaning decision is logged and mirrored in
  docs/data_quality.md.
- Verifiable: prints row counts before/after and spot-checks joins.

Usage
-----
    python etl/load.py --data-dir data --db-url postgresql://user:pass@host:5432/road_safety

Cleaning rules (see docs/data_quality.md for the full log)
----------------------------------------------------------
- severity: kept as int 1/2/3 (fatal/serious/slight); rows with other
  values are dropped and counted.
- Coded fields (weather, lighting, road surface, road class, urban/rural,
  casualty class, sex, vehicle type, manoeuvre, propulsion, age band)
  are DECODED to human-readable labels so Power BI reports are
  meaningful; unmapped codes become "Unknown".
- age / age_of_driver: -1, 0, 99, 999 treated as UNKNOWN -> NULL.
- accident_time: "HH:MM" (or legacy "HHMM") text -> TIME; invalid -> NULL.
- lat/long: out-of-range or blank -> NULL.
- vru_flag: True when casualty_class is 1 (pedestrian) or 2 (cyclist).
- age_band: 5-year bands for reporting; "Unknown" for missing.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("etl")

# ------------------------------------------------------------------
# DfT "Road Safety Data" reference mappings (code -> label)
# Source: data.dft.gov.uk code tables. Codes not listed here are
# rendered as "Unknown" so no row is silently dropped.
# ------------------------------------------------------------------
WEATHER_CONDITIONS = {
    1: "Fine no precipitation",
    2: "Fine with precipitation",
    3: "Other precipitation",
    4: "Fog or mist",
    5: "Cloudy, overcast",
    6: "Snow, hail, sleet, blowing snow",
    7: "Rain, showers, sleet, hail",
    8: "Thunder",
    9: "Unknown",
}

LIGHT_CONDITIONS = {
    1: "Daylight",
    4: "Darkness - lights lit",
    5: "Darkness - lights unlit",
    6: "Darkness - no lights",
    7: "Twilight",
    -1: "Unknown",
}

ROAD_SURFACE_CONDITIONS = {
    1: "Dry",
    2: "Wet or slippery",
    3: "Snow or ice",
    4: "Flooded",
    5: "Oil, gravel, or other obstruction",
    9: "Unknown",
}

FIRST_ROAD_CLASS = {
    1: "Motorway",
    2: "Trunk road",
    3: "Primary distribution road",
    4: "Secondary distribution road",
    5: "Territorial road",
    6: "Unknown",
    -1: "Unknown",
}

URBAN_RURAL = {
    1: "Urban",
    2: "Rural",
    3: "Unknown",
    -1: "Unknown",
}

CASUALTY_CLASS = {
    1: "Pedestrian",
    2: "Cyclist",
    3: "Motorist",
    4: "Passenger",
    5: "Motorcyclist",
    6: "Moped rider",
    7: "Other",
    -1: "Unknown",
}

# Casualty classes that count as a Vulnerable Road User (VRU):
# pedestrians and cyclists. Motorists/passengers/motorcyclists are not.
VRU_CLASSES = {1, 2}

SEX_OF_CASUALTY = {
    1: "Male",
    2: "Female",
    9: "Unknown",
    -1: "Unknown",
}

VEHICLE_TYPE = {
    1: "Car",
    2: "Taxi/private hire vehicle",
    3: "Bus or coach",
    4: "LGV (van, pickup, 3W)",
    5: "Motorcycle 50cc - 250cc",
    6: "Motorcycle 251cc - 400cc",
    7: "Motorcycle 401cc - 675cc",
    8: "Motorcycle 676cc and above",
    9: "Motorcycle (unknown size)",
    10: "Moped",
    11: "Agricultural tractor",
    12: "LGV (other)",
    13: "HGV",
    14: "PSV (other)",
    15: "Motorcycle (other)",
    16: "Other vehicle",
    17: "Unknown",
    18: "Unknown",
    19: "Unknown",
    20: "Unknown",
    21: "Unknown",
    33: "Unknown",
    90: "Unknown",
    97: "Unknown",
    98: "Unknown",
    99: "Unknown",
}

VEHICLE_MANOEUVRE = {
    1: "Overtaking",
    2: "Turning left",
    3: "Turning right",
    4: "Turning circle",
    5: "U-turn",
    6: "Reversing",
    7: "Accelerating",
    8: "Slowing or stopping",
    9: "Going straight",
    10: "Lane change",
    11: "Starting from stopped position",
    12: "Turning left (other)",
    13: "Turning right (other)",
    14: "Overtaking (other)",
    15: "Unknown",
    16: "Unknown",
    17: "Unknown",
    18: "Unknown",
    19: "Unknown",
    99: "Unknown",
    -1: "Unknown",
}

PROPULSION_CODE = {
    1: "Petrol",
    2: "Diesel",
    3: "Electric",
    4: "LPG",
    5: "Hybrid",
    6: "Hydrogen",
    7: "Other",
    8: "Unknown",
    9: "Unknown",
    10: "Unknown",
    12: "Unknown",
    -1: "Unknown",
}

AGE_BAND_OF_DRIVER = {
    1: "0-1",
    2: "2-5",
    3: "6-10",
    4: "11-14",
    5: "15-17",
    6: "17-20",
    7: "21-24",
    8: "25-29",
    9: "30-34",
    10: "35-39",
    11: "40-44",
    12: "45-49",
    13: "50-54",
    14: "55-59",
    15: "60-64",
    16: "65-69",
    17: "70-74",
    18: "75-79",
    19: "80+",
    -1: "Unknown",
}

SEX_OF_DRIVER = {
    1: "Male",
    2: "Female",
    3: "Unknown",
    -1: "Unknown",
}

# Unknown / missing codes for numeric fields.
AGE_UNKNOWN = {-1, 0, 99, 999}


# ------------------------------------------------------------------
# Transform helpers
# ------------------------------------------------------------------
def clean_severity(series: pd.Series) -> pd.Series:
    """Keep only valid severity codes (1/2/3); NaN otherwise."""
    s = pd.to_numeric(series, errors="coerce").astype("Int64")
    return s.where(s.isin([1, 2, 3]))


def clean_age(series: pd.Series) -> pd.Series:
    """Map unknown-age codes (-1/0/99/999) to NULL."""
    s = pd.to_numeric(series, errors="coerce").astype("Int64")
    return s.where(~s.isin(AGE_UNKNOWN))


def age_band(age: pd.Series) -> pd.Series:
    """5-year age bands for reporting; 'Unknown' for missing."""
    def band(v):
        if pd.isna(v):
            return "Unknown"
        lo = int(v // 5 * 5)
        return f"{lo}-{lo + 4}"
    return age.map(band)


def clean_time(series: pd.Series) -> pd.Series:
    """Convert 'HH:MM' (new DfT spec) or legacy 'HHMM' to 'HH:MM:SS'; NULL if invalid."""
    def conv(v):
        if pd.isna(v):
            return None
        s = str(v).strip()
        # New spec: "HH:MM" (optionally "HH:MM:SS")
        if ":" in s:
            parts = s.split(":")
            if len(parts) < 2:
                return None
            try:
                hh, mm = int(parts[0]), int(parts[1])
                ss = int(parts[2]) if len(parts) > 2 else 0
            except ValueError:
                return None
        else:
            # Legacy: "HHMM"
            s = s.zfill(4)
            if len(s) != 4 or not s.isdigit():
                return None
            hh, mm = int(s[:2]), int(s[2:])
            ss = 0
        if hh > 23 or mm > 59 or ss > 59:
            return None
        return f"{hh:02d}:{mm:02d}:{ss:02d}"
    return series.map(conv)


def clean_coord(series: pd.Series, lo: float, hi: float) -> pd.Series:
    """NULL out-of-range or non-numeric coordinates."""
    s = pd.to_numeric(series, errors="coerce")
    return s.where((s >= lo) & (s <= hi))


def is_vru(casualty_class: pd.Series) -> pd.Series:
    """Flag vulnerable road users: casualty_class 1 (pedestrian) or 2 (cyclist)."""
    s = pd.to_numeric(casualty_class, errors="coerce").astype("Int64")
    return s.isin(VRU_CLASSES)


def decode_code(series: pd.Series, mapping: dict) -> pd.Series:
    """Map a coded integer column to human-readable labels.

    Unmapped / non-numeric codes become 'Unknown' so no row is dropped.
    """
    s = pd.to_numeric(series, errors="coerce").astype("Int64")
    return s.map(mapping).fillna("Unknown")


# ------------------------------------------------------------------
# Load helpers
# ------------------------------------------------------------------
def df_to_rows(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame to a list of dicts, mapping NaN -> None.

    We cast to object first: on a float column, ``where(..., None)`` would
    otherwise cast ``None`` back to ``NaN`` and the value would reach the
    database as a float NaN instead of a SQL NULL.
    """
    mask = pd.notna(df)
    return df.astype(object).where(mask, None).to_dict(orient="records")


def bulk_insert(cur, table: str, rows: list[dict], columns: list[str]) -> int:
    if not rows:
        return 0
    psycopg2.extras.execute_values(
        cur,
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s",
        [tuple(r[c] for c in columns) for r in rows],
        page_size=5000,
    )
    return len(rows)


# ------------------------------------------------------------------
# Main ETL
# ------------------------------------------------------------------
def run(data_dir: Path, db_url: str) -> None:
    accidents_path = data_dir / "accidents.csv"
    vehicles_path = data_dir / "vehicles.csv"
    casualties_path = data_dir / "casualties.csv"
    for p in (accidents_path, vehicles_path, casualties_path):
        if not p.exists():
            log.error("Missing input file: %s", p)
            sys.exit(1)

    log.info("Reading raw CSVs from %s", data_dir)
    acc = pd.read_csv(accidents_path, dtype=str)
    veh = pd.read_csv(vehicles_path, dtype=str)
    cas = pd.read_csv(casualties_path, dtype=str)
    log.info("Raw rows -> accidents=%d vehicles=%d casualties=%d",
             len(acc), len(veh), len(cas))

    # ---------------- dim_date ----------------
    # New DfT spec: 'date' column, DD/MM/YYYY format.
    dates = pd.to_datetime(acc["date"], errors="coerce", dayfirst=True)
    valid_dates = dates.dropna()
    dim_date = pd.DataFrame({
        "date_key": valid_dates.dt.strftime("%Y%m%d").astype(int),
        "full_date": valid_dates.dt.date,
        "year": valid_dates.dt.year,
        "month": valid_dates.dt.month,
        "month_name": valid_dates.dt.strftime("%B"),
        "quarter": valid_dates.dt.quarter,
        "day_of_week": valid_dates.dt.dayofweek + 1,  # 1=Mon
        "day_of_week_name": valid_dates.dt.strftime("%A"),
        "is_weekend": valid_dates.dt.dayofweek >= 5,
    }).drop_duplicates("date_key").reset_index(drop=True)
    log.info("dim_date -> %d distinct dates", len(dim_date))

    # ---------------- dim_location ----------------
    # Key the dimension on the categorical road/geography attributes.
    # Coordinates are per-accident, so we keep a representative (first)
    # value per combination rather than one row per accident.
    # Coded fields are decoded to labels BEFORE keying, so the dimension
    # stores human-readable values.
    # NOTE: In the 2025 DfT extract, `local_authority_district` is 100% `-1`
    # (deprecated). The real geography is in `local_authority_ons_district`
    # (ONS codes: E06=England, E08=Scotland, E09=Wales, S12=Scottish council
    # areas, W06=Wales, E07=London boroughs). We store the ONS code as the
    # district value; `-1` becomes "Unknown".
    district_raw = acc.get("local_authority_ons_district")
    if district_raw is None:
        district_raw = acc.get("local_authority_district")
    acc["district"] = (
        district_raw.astype(str).str.strip()
        .replace({"-1": "Unknown", "nan": "Unknown", "": "Unknown"})
    )
    acc["road_class"] = decode_code(acc.get("first_road_class"), FIRST_ROAD_CLASS)
    acc["urban_rural"] = decode_code(acc.get("urban_or_rural_area"), URBAN_RURAL)
    acc["police_force"] = acc.get("police_force")

    key_cols = ["district", "road_class", "urban_rural", "police_force"]
    loc_src = pd.DataFrame({
        "district": acc["district"],
        "road_class": acc["road_class"],
        "urban_rural": acc["urban_rural"],
        "police_force": acc["police_force"],
        "lat": clean_coord(acc.get("latitude"), -90, 90),
        "long": clean_coord(acc.get("longitude"), -180, 180),
    })
    loc = (
        loc_src.groupby(key_cols, dropna=False)
        .agg(lat=("lat", "first"), long=("long", "first"))
        .reset_index()
        .reset_index(drop=True)
    )
    loc["location_key"] = loc.index + 1
    log.info("dim_location -> %d distinct locations", len(loc))

    # ---------------- fact_accident ----------------
    acc["accident_index"] = acc["collision_index"]
    acc["severity"] = clean_severity(acc["collision_severity"])
    acc["date_key"] = dates.dt.strftime("%Y%m%d").astype("Int64")
    acc["accident_time"] = clean_time(acc.get("time"))
    acc["weather"] = decode_code(acc.get("weather_conditions"), WEATHER_CONDITIONS)
    acc["lighting"] = decode_code(acc.get("light_conditions"), LIGHT_CONDITIONS)
    acc["road_surface"] = decode_code(acc.get("road_surface_conditions"), ROAD_SURFACE_CONDITIONS)
    acc["num_vehicles"] = pd.to_numeric(acc.get("number_of_vehicles"), errors="coerce").astype("Int64")
    acc["num_casualties"] = pd.to_numeric(acc.get("number_of_casualties"), errors="coerce").astype("Int64")
    acc["speed_limit"] = pd.to_numeric(acc.get("speed_limit"), errors="coerce").astype("Int64")

    # Map each accident to its location_key
    loc_lookup = loc.set_index(key_cols)["location_key"].to_dict()
    acc["location_key"] = [
        loc_lookup.get((d, r, u, p), None)
        for d, r, u, p in zip(
            acc["district"], acc["road_class"],
            acc["urban_rural"], acc["police_force"],
        )
    ]

    # Drop accidents we cannot place in time or space
    before = len(acc)
    acc = acc.dropna(subset=["date_key", "location_key", "severity"]).reset_index(drop=True)
    log.info("fact_accident -> %d (dropped %d unplaceable)", len(acc), before - len(acc))

    # ---------------- fact_casualty ----------------
    # casualty_reference is a per-collision counter (1,2,3...), not globally
    # unique. Build a globally-unique surrogate key from collision_index + ref.
    cas["casualty_rec"] = cas["collision_index"].astype(str) + "_" + cas["casualty_reference"].astype(str)
    cas["accident_index"] = cas["collision_index"]
    cas["severity"] = clean_severity(cas["casualty_severity"])
    cas["age"] = clean_age(cas.get("age_of_casualty"))
    cas["age_band"] = age_band(cas["age"])
    cas["sex"] = decode_code(cas.get("sex_of_casualty"), SEX_OF_CASUALTY)
    cas["casualty_type"] = decode_code(cas.get("casualty_class"), CASUALTY_CLASS)
    cas["vru_flag"] = is_vru(cas.get("casualty_class"))

    # Inherit date_key + location_key from the parent accident
    acc_lookup = acc.set_index("accident_index")[["date_key", "location_key"]].to_dict("index")
    cas["date_key"] = cas["accident_index"].map(lambda a: acc_lookup.get(a, {}).get("date_key"))
    cas["location_key"] = cas["accident_index"].map(lambda a: acc_lookup.get(a, {}).get("location_key"))

    before = len(cas)
    cas = cas.dropna(subset=["accident_index", "date_key", "location_key", "severity"]).reset_index(drop=True)
    log.info("fact_casualty -> %d (dropped %d orphaned)", len(cas), before - len(cas))

    # ---------------- fact_vehicle ----------------
    # vehicle_reference is a per-collision counter (1,2,3...), not globally
    # unique. Build a globally-unique surrogate key from collision_index + ref.
    veh["vehicle_rec"] = veh["collision_index"].astype(str) + "_" + veh["vehicle_reference"].astype(str)
    veh["accident_index"] = veh["collision_index"]
    veh["vehicle_type"] = decode_code(veh.get("vehicle_type"), VEHICLE_TYPE)
    veh["manoeuvre"] = decode_code(veh.get("vehicle_manoeuvre"), VEHICLE_MANOEUVRE)
    veh["engine_size_cc"] = pd.to_numeric(veh.get("engine_capacity_cc"), errors="coerce").astype("Int64")
    veh["propellant"] = decode_code(veh.get("propulsion_code"), PROPULSION_CODE)
    veh["driver_age_band"] = decode_code(veh.get("age_band_of_driver"), AGE_BAND_OF_DRIVER)
    veh["driver_sex"] = decode_code(veh.get("sex_of_driver"), SEX_OF_DRIVER)
    before = len(veh)
    veh = veh.dropna(subset=["accident_index"]).reset_index(drop=True)
    log.info("fact_vehicle -> %d (dropped %d orphaned)", len(veh), before - len(veh))

    # ---------------- Load ----------------
    log.info("Connecting to database and loading...")
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # Truncate in FK order (children first)
        cur.execute("TRUNCATE fact_vehicle, fact_casualty, fact_accident, "
                    "dim_location, dim_date RESTART IDENTITY CASCADE;")

        bulk_insert(cur, "dim_date", df_to_rows(dim_date),
                    ["date_key", "full_date", "year", "month", "month_name",
                     "quarter", "day_of_week", "day_of_week_name", "is_weekend"])
        bulk_insert(cur, "dim_location", df_to_rows(loc),
                    ["location_key", "district", "road_class", "urban_rural",
                     "police_force", "lat", "long"])
        bulk_insert(cur, "fact_accident", df_to_rows(acc),
                    ["accident_index", "date_key", "location_key", "accident_time",
                     "severity", "weather", "lighting", "road_surface",
                     "num_vehicles", "num_casualties", "speed_limit"])
        bulk_insert(cur, "fact_casualty", df_to_rows(cas),
                    ["casualty_rec", "accident_index", "date_key", "location_key",
                     "age", "age_band", "sex", "casualty_type", "severity",
                     "vru_flag"])
        bulk_insert(cur, "fact_vehicle", df_to_rows(veh),
                    ["vehicle_rec", "accident_index", "vehicle_type", "manoeuvre",
                     "engine_size_cc", "propellant", "driver_age_band",
                     "driver_sex"])

        conn.commit()
        log.info("COMMIT OK")
    except Exception:
        conn.rollback()
        log.exception("ROLLBACK — load failed")
        raise
    finally:
        cur.close()
        conn.close()

    log.info("ETL complete.")


def main() -> None:
    ap = argparse.ArgumentParser(description="DfT Road Safety Data -> star schema ETL")
    ap.add_argument("--data-dir", default="data", help="Directory with the 3 CSVs")
    ap.add_argument("--db-url", required=True, help="PostgreSQL connection string")
    args = ap.parse_args()
    run(Path(args.data_dir), args.db_url)


if __name__ == "__main__":
    main()
