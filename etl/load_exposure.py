"""Phase B — Exposure-adjusted rates ETL.

Loads DfT exposure / validation / cost tables (ODS) into PostgreSQL:

  exposure_vehicle_km        national + LA vehicle-km (TRA0201/0202/0204/8904/8905/0401/0412)
  exposure_licensed_vehicles licensed vehicle counts (VEH0101a)
  ras0201_numbers            DfT published casualty counts (validation)
  ras0201_rates              DfT published casualty rates (validation)
  ras4001_cost_per_casualty  cost per casualty / collision (Phase F)
  ras4001_total_cost         total cost of collisions by severity (Phase F)

All vehicle-km normalised to MILLION vehicle-km.

Run:  python etl/load_exposure.py
"""
from __future__ import annotations

import os
import re
import sys

import pandas as pd
import psycopg2
import psycopg2.extras

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPOSURE_DIR = os.path.join(BASE, "data", "exposure")
DSN = "postgresql://postgres:postgres@localhost:5432/road_safety"

# ---------------------------------------------------------------------------
# ODS reading helpers
# ---------------------------------------------------------------------------

YEAR_RE = re.compile(r"^\s*(\d{4})")


def _is_year_name(col) -> bool:
    """True if a column *name* looks like a calendar year (1900-2030).
    Handles names like '2000 [note 1]' or '2021 [note 3]'."""
    m = YEAR_RE.match(str(col))
    if not m:
        return False
    return 1900 <= int(m.group(1)) <= 2030


def _year_from_name(col) -> int:
    """Extract the 4-digit year from a column name like '2000 [note 1]'."""
    m = YEAR_RE.match(str(col))
    if not m:
        raise ValueError(f"Cannot extract year from column name: {col!r}")
    return int(m.group(1))


def read_ods_sheet(path: str, sheet: str, marker: str) -> pd.DataFrame:
    """Read an ODS data sheet, auto-detecting the header row via a marker
    string that appears in the first column of the header row."""
    raw = pd.read_excel(path, engine="odf", sheet_name=sheet, header=None)
    header_row = None
    for i in range(len(raw)):
        val = raw.iloc[i, 0]
        if isinstance(val, str) and val.strip() == marker:
            header_row = i
            break
    if header_row is None:
        raise ValueError(f"Header marker {marker!r} not found in sheet {sheet!r}")
    header = [str(x).strip() if pd.notna(x) else f"col_{j}"
              for j, x in enumerate(raw.iloc[header_row].tolist())]
    data = raw.iloc[header_row + 1:].copy()
    data.columns = header
    data = data.reset_index(drop=True)
    # strip whitespace from string data values (ODS pads with spaces)
    for c in data.columns:
        if data[c].dtype == object:
            data[c] = data[c].map(lambda v: v.strip() if isinstance(v, str) else v)
    # drop fully-empty rows
    data = data.dropna(how="all").reset_index(drop=True)
    return data


def _unit_factor(df: pd.DataFrame) -> float:
    """Return multiplier to convert the table's unit to MILLION vehicle-km."""
    if "Units" in df.columns:
        unit = str(df["Units"].dropna().iloc[0]).lower() if df["Units"].notna().any() else ""
    else:
        unit = ""
    if "billion" in unit:
        return 1000.0
    return 1.0


def _melt_wide_years(df: pd.DataFrame, id_cols: list[str]) -> pd.DataFrame:
    """Melt year-named columns (Orientation B) into long format."""
    year_cols = [c for c in df.columns if _is_year_name(c)]
    keep = [c for c in id_cols if c in df.columns]
    sub = df[keep + year_cols].copy()
    melted = sub.melt(id_vars=keep, value_vars=year_cols,
                      var_name="year", value_name="value")
    melted["year"] = melted["year"].map(_year_from_name)
    return melted


def _melt_metric_cols(df: pd.DataFrame, year_col: str,
                      exclude: set[str]) -> pd.DataFrame:
    """Melt metric columns (Orientation A: years are a data column)."""
    metric_cols = [c for c in df.columns
                   if c not in exclude and c != year_col and not _is_year_name(c)]
    keep = [year_col]
    sub = df[keep + metric_cols].copy()
    melted = sub.melt(id_vars=keep, value_vars=metric_cols,
                      var_name="metric", value_name="value")
    melted["year"] = melted[year_col].astype(str).str.extract(r"(\d{4})")[0].astype(float).astype(int)
    return melted


# ---------------------------------------------------------------------------
# Per-table parsers -> standard long DataFrames
# ---------------------------------------------------------------------------

def parse_tra0201() -> pd.DataFrame:
    """Vehicle-km by vehicle type (national, GB)."""
    df = read_ods_sheet("tra0201_km_by_vehicle_type.ods", "TRA0201", "Year")
    factor = _unit_factor(df)
    m = _melt_metric_cols(df, "Year", exclude={"Notes", "Units"})
    out = pd.DataFrame({
        "year": m["year"],
        "geo_code": "GB", "geo_name": "Great Britain",
        "vehicle_type": m["metric"], "road_class": "All",
        "vehicle_km_million": pd.to_numeric(m["value"], errors="coerce") * factor,
        "source_table": "TRA0201",
    })
    return out.dropna(subset=["vehicle_km_million"])


def parse_tra0202() -> pd.DataFrame:
    """Vehicle-km by road class (national, GB)."""
    df = read_ods_sheet("tra0202_km_by_road_class.ods", "TRA0202", "Year")
    factor = _unit_factor(df)
    m = _melt_metric_cols(df, "Year", exclude={"Notes", "Units"})
    out = pd.DataFrame({
        "year": m["year"],
        "geo_code": "GB", "geo_name": "Great Britain",
        "vehicle_type": "All", "road_class": m["metric"],
        "vehicle_km_million": pd.to_numeric(m["value"], errors="coerce") * factor,
        "source_table": "TRA0202",
    })
    return out.dropna(subset=["vehicle_km_million"])


def parse_tra0204() -> pd.DataFrame:
    """Vehicle-km by vehicle type x road type (national, GB).
    TRA0204 is a 4D cube (Road Type x Vehicle x Road Management x Rural Urban
    Classification).  Filter to Road Management='All' AND Rural Urban
    Classification='All' to avoid double-counting."""
    df = read_ods_sheet("tra0204_km_by_vehicle_and_road_type.ods", "TRA0204", "Road Type")
    factor = _unit_factor(df)
    # Filter the 4D cube to the 'All' slices to avoid double-counting
    if "Road Management" in df.columns:
        df = df[df["Road Management"].astype(str).str.strip() == "All"]
    if "Rural Urban Classification" in df.columns:
        df = df[df["Rural Urban Classification"].astype(str).str.strip() == "All"]
    df = df.reset_index(drop=True)
    id_cols = [c for c in ("Road Type", "Vehicle") if c in df.columns]
    m = _melt_wide_years(df, id_cols)
    out = pd.DataFrame({
        "year": m["year"],
        "geo_code": "GB", "geo_name": "Great Britain",
        "vehicle_type": m.get("Vehicle", "All"),
        "road_class": m.get("Road Type", "All"),
        "vehicle_km_million": pd.to_numeric(m["value"], errors="coerce") * factor,
        "source_table": "TRA0204",
    })
    return out.dropna(subset=["vehicle_km_million"])


def parse_tra8904() -> pd.DataFrame:
    """Vehicle-km by local authority (GB, incl. aggregate rows)."""
    df = read_ods_sheet("tra8904_km_by_local_authority.ods", "TRA8904",
                        "Local Authority or Region Code")
    factor = _unit_factor(df)
    code_col = "Local Authority or Region Code"
    name_col = "Local Authority"
    id_cols = [c for c in (code_col, name_col) if c in df.columns]
    m = _melt_wide_years(df, id_cols)
    out = pd.DataFrame({
        "year": m["year"],
        "geo_code": m[code_col].astype(str).str.strip(),
        "geo_name": m[name_col].astype(str).str.strip() if name_col in m.columns else "",
        "vehicle_type": "All", "road_class": "All",
        "vehicle_km_million": pd.to_numeric(m["value"], errors="coerce") * factor,
        "source_table": "TRA8904",
    })
    return out.dropna(subset=["vehicle_km_million"])


def parse_tra8905() -> pd.DataFrame:
    """Vehicle-km by local authority x vehicle type."""
    df = read_ods_sheet("tra8905_km_by_la_and_vehicle_type.ods", "TRA8905", "Vehicle")
    factor = _unit_factor(df)
    code_col = "Local Authority or Region Code"
    name_col = "Local Authority"
    id_cols = [c for c in ("Vehicle", code_col, name_col) if c in df.columns]
    m = _melt_wide_years(df, id_cols)
    out = pd.DataFrame({
        "year": m["year"],
        "geo_code": m[code_col].astype(str).str.strip(),
        "geo_name": m[name_col].astype(str).str.strip() if name_col in m.columns else "",
        "vehicle_type": m["Vehicle"].astype(str).str.strip(),
        "road_class": "All",
        "vehicle_km_million": pd.to_numeric(m["value"], errors="coerce") * factor,
        "source_table": "TRA8905",
    })
    return out.dropna(subset=["vehicle_km_million"])


def parse_tra0401() -> pd.DataFrame:
    """Pedal cycle traffic (national, GB) — use the km column only."""
    df = read_ods_sheet("tra0401_pedal_cycle_traffic.ods", "TRA0401", "Year")
    km_col = next((c for c in df.columns if "kilometre" in c.lower() or "kilometer" in c.lower()), None)
    if km_col is None:
        raise ValueError("TRA0401: no pedal-cycle km column found")
    unit = str(df["Units"].dropna().iloc[0]).lower() if "Units" in df.columns and df["Units"].notna().any() else ""
    factor = 1000.0 if "billion" in unit else 1.0
    out = pd.DataFrame({
        "year": df["Year"].astype(str).str.extract(r"(\d{4})")[0].astype(float).astype(int),
        "geo_code": "GB", "geo_name": "Great Britain",
        "vehicle_type": "Pedal Cycle", "road_class": "All",
        "vehicle_km_million": pd.to_numeric(df[km_col], errors="coerce") * factor,
        "source_table": "TRA0401",
    })
    return out.dropna(subset=["vehicle_km_million"])


def parse_tra0412() -> pd.DataFrame:
    """Pedal cycle traffic by road class (national, GB)."""
    df = read_ods_sheet("tra0412_pedal_cycle_by_road_class.ods", "TRA0412", "Year")
    factor = _unit_factor(df)
    m = _melt_metric_cols(df, "Year", exclude={"Notes", "Units"})
    out = pd.DataFrame({
        "year": m["year"],
        "geo_code": "GB", "geo_name": "Great Britain",
        "vehicle_type": "Pedal Cycle", "road_class": m["metric"],
        "vehicle_km_million": pd.to_numeric(m["value"], errors="coerce") * factor,
        "source_table": "TRA0412",
    })
    return out.dropna(subset=["vehicle_km_million"])


def parse_veh0101() -> pd.DataFrame:
    """Licensed vehicles by geography x vehicle type (quarterly -> annual).
    VEH0101 is quarterly; we take the Q4 (year-end) snapshot as the annual
    figure, which is the standard convention for vehicle population counts."""
    df = read_ods_sheet("veh0101_licensed_vehicles.ods", "VEH0101a_Lic", "Geography")
    veh_cols = [c for c in df.columns
                if c not in ("Geography", "Date", "Units") and not _is_year_name(c)]
    m = df[["Geography", "Date"] + veh_cols].melt(
        id_vars=["Geography", "Date"], value_vars=veh_cols,
        var_name="vehicle_type", value_name="vehicles_thousand")
    m["year"] = m["Date"].astype(str).str.extract(r"(\d{4})")[0].astype(float).astype(int)
    m["quarter"] = m["Date"].astype(str).str.extract(r"Q(\d)")[0].astype(int)
    # Keep only Q4 (year-end) as the annual snapshot
    m = m[m["quarter"] == 4]
    out = pd.DataFrame({
        "year": m["year"],
        "geo_name": m["Geography"].astype(str).str.strip(),
        "vehicle_type": m["vehicle_type"],
        "vehicles_thousand": pd.to_numeric(m["vehicles_thousand"], errors="coerce"),
        "source_table": "VEH0101a",
    })
    return out.dropna(subset=["vehicles_thousand"])


def parse_ras0201_numbers() -> pd.DataFrame:
    df = read_ods_sheet("ras0201_numbers_and_rates.ods", "Numbers", "Road user type")
    m = _melt_wide_years(df, ["Road user type", "Severity [note 1]"])
    out = pd.DataFrame({
        "year": m["year"],
        "road_user_type": m["Road user type"].astype(str).str.strip(),
        "severity": m["Severity [note 1]"].astype(str).str.strip(),
        "count": pd.to_numeric(m["value"], errors="coerce"),
    })
    return out.dropna(subset=["count"])


def parse_ras0201_rates() -> pd.DataFrame:
    df = read_ods_sheet("ras0201_numbers_and_rates.ods", "Rates", "Road user type")
    m = _melt_wide_years(df, ["Road user type", "Severity [note 1]", "Rate unit [note 2]"])
    out = pd.DataFrame({
        "year": m["year"],
        "road_user_type": m["Road user type"].astype(str).str.strip(),
        "severity": m["Severity [note 1]"].astype(str).str.strip(),
        "rate_unit": m["Rate unit [note 2]"].astype(str).str.strip(),
        "rate_value": pd.to_numeric(m["value"], errors="coerce"),
    })
    return out.dropna(subset=["rate_value"])


def parse_ras4001_avg() -> pd.DataFrame:
    df = read_ods_sheet("ras4001_cost_of_prevention.ods", "Average_value", "Collision data year")
    out = pd.DataFrame({
        "collision_year": df["Collision data year"].astype(int),
        "price_year": df["Price year"].astype(int),
        "severity": df["Severity"].astype(str).str.strip(),
        "cost_per_casualty": pd.to_numeric(df["Cost per casualty (\u00a3)"], errors="coerce"),
        "cost_per_collision": pd.to_numeric(df["Cost per collision (\u00a3)"], errors="coerce"),
    })
    return out


def parse_ras4001_total() -> pd.DataFrame:
    df = read_ods_sheet("ras4001_cost_of_prevention.ods", "Total_value", "Collision data year")
    colmap = {}
    for c in df.columns:
        cl = c.lower()
        if "lost output" in cl:
            colmap["lost_output_mil"] = c
        elif "medical" in cl:
            colmap["medical_mil"] = c
        elif "human costs" in cl:
            colmap["human_costs_mil"] = c
        elif "police" in cl:
            colmap["police_mil"] = c
        elif "insurance" in cl:
            colmap["insurance_mil"] = c
        elif "damage to property" in cl:
            colmap["property_damage_mil"] = c
        elif cl.strip() == "total (\u00a3 million)" or cl.strip().startswith("total"):
            colmap["total_mil"] = c
    out = pd.DataFrame({
        "collision_year": df["Collision data year"].astype(int),
        "price_year": df["Price year"].astype(int),
        "severity": df["Severity [note 4]"].astype(str).str.strip() if "Severity [note 4]" in df.columns
                    else df["Severity"].astype(str).str.strip(),
    })
    for key, col in colmap.items():
        out[key] = pd.to_numeric(df[col], errors="coerce")
    return out


# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

DDL = """
DROP TABLE IF EXISTS exposure_vehicle_km;
CREATE TABLE exposure_vehicle_km (
    year               INT            NOT NULL,
    geo_code           TEXT           NOT NULL DEFAULT 'GB',
    geo_name           TEXT           NOT NULL DEFAULT 'Great Britain',
    vehicle_type       TEXT           NOT NULL DEFAULT 'All',
    road_class         TEXT           NOT NULL DEFAULT 'All',
    vehicle_km_million NUMERIC(18,4)  NOT NULL,
    source_table       TEXT           NOT NULL,
    PRIMARY KEY (year, geo_code, vehicle_type, road_class, source_table)
);
CREATE INDEX idx_exp_km_year ON exposure_vehicle_km (year);
CREATE INDEX idx_exp_km_geo  ON exposure_vehicle_km (geo_code);

DROP TABLE IF EXISTS exposure_licensed_vehicles;
CREATE TABLE exposure_licensed_vehicles (
    year              INT           NOT NULL,
    geo_name          TEXT          NOT NULL,
    vehicle_type      TEXT          NOT NULL,
    vehicles_thousand NUMERIC(18,4) NOT NULL,
    source_table      TEXT          NOT NULL DEFAULT 'VEH0101a',
    PRIMARY KEY (year, geo_name, vehicle_type, source_table)
);
CREATE INDEX idx_lic_year ON exposure_licensed_vehicles (year);

DROP TABLE IF EXISTS ras0201_numbers;
CREATE TABLE ras0201_numbers (
    year           INT           NOT NULL,
    road_user_type TEXT          NOT NULL,
    severity       TEXT          NOT NULL,
    count          NUMERIC(18,4) NOT NULL,
    PRIMARY KEY (year, road_user_type, severity)
);

DROP TABLE IF EXISTS ras0201_rates;
CREATE TABLE ras0201_rates (
    year           INT           NOT NULL,
    road_user_type TEXT          NOT NULL,
    severity       TEXT          NOT NULL,
    rate_unit      TEXT          NOT NULL,
    rate_value     NUMERIC(18,6) NOT NULL,
    PRIMARY KEY (year, road_user_type, severity, rate_unit)
);

DROP TABLE IF EXISTS ras4001_cost_per_casualty;
CREATE TABLE ras4001_cost_per_casualty (
    collision_year   INT           NOT NULL,
    price_year       INT           NOT NULL,
    severity         TEXT          NOT NULL,
    cost_per_casualty NUMERIC(18,4),
    cost_per_collision NUMERIC(18,4),
    PRIMARY KEY (collision_year, price_year, severity)
);

DROP TABLE IF EXISTS ras4001_total_cost;
CREATE TABLE ras4001_total_cost (
    collision_year     INT           NOT NULL,
    price_year         INT           NOT NULL,
    severity           TEXT          NOT NULL,
    lost_output_mil    NUMERIC(18,4),
    medical_mil        NUMERIC(18,4),
    human_costs_mil    NUMERIC(18,4),
    police_mil         NUMERIC(18,4),
    insurance_mil      NUMERIC(18,4),
    property_damage_mil NUMERIC(18,4),
    total_mil          NUMERIC(18,4),
    PRIMARY KEY (collision_year, price_year, severity)
);
"""


def _load_df(cur, df: pd.DataFrame, table: str) -> int:
    if df.empty:
        return 0
    cols = list(df.columns)
    placeholders = ", ".join(["%s"] * len(cols))
    colsql = ", ".join(cols)
    rows = df.where(pd.notna(df), None).itertuples(index=False, name=None)
    psycopg2.extras.execute_values(
        cur,
        f"INSERT INTO {table} ({colsql}) VALUES %s ON CONFLICT DO NOTHING",
        [tuple(r) for r in rows],
        template=None,
        page_size=5000,
    )
    return len(df)


def main() -> None:
    os.chdir(EXPOSURE_DIR)
    conn = psycopg2.connect(DSN)
    conn.autocommit = False
    cur = conn.cursor()

    print("Applying DDL...")
    cur.execute(DDL)
    conn.commit()

    jobs = [
        ("exposure_vehicle_km", parse_tra0201()),
        ("exposure_vehicle_km", parse_tra0202()),
        ("exposure_vehicle_km", parse_tra0204()),
        ("exposure_vehicle_km", parse_tra8904()),
        ("exposure_vehicle_km", parse_tra8905()),
        ("exposure_vehicle_km", parse_tra0401()),
        ("exposure_vehicle_km", parse_tra0412()),
        ("exposure_licensed_vehicles", parse_veh0101()),
        ("ras0201_numbers", parse_ras0201_numbers()),
        ("ras0201_rates", parse_ras0201_rates()),
        ("ras4001_cost_per_casualty", parse_ras4001_avg()),
        ("ras4001_total_cost", parse_ras4001_total()),
    ]

    for table, df in jobs:
        n = _load_df(cur, df, table)
        print(f"  loaded {n:6d} rows -> {table}")
    conn.commit()

    # verification
    print("\nVerification (row counts):")
    for t in ["exposure_vehicle_km", "exposure_licensed_vehicles",
              "ras0201_numbers", "ras0201_rates",
              "ras4001_cost_per_casualty", "ras4001_total_cost"]:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"  {t:32s} {cur.fetchone()[0]:>8,}")

    print("\nexposure_vehicle_km by source_table:")
    cur.execute("SELECT source_table, COUNT(*), MIN(year), MAX(year) "
                "FROM exposure_vehicle_km GROUP BY source_table ORDER BY source_table")
    for r in cur.fetchall():
        print(f"  {r[0]:10s} rows={r[1]:>6,}  years {r[2]}-{r[3]}")

    print("\nSample: GB all-vehicle km by road class, 2021-2025 (TRA0202):")
    cur.execute("""
        SELECT year, road_class, vehicle_km_million
        FROM exposure_vehicle_km
        WHERE source_table='TRA0202' AND geo_code='GB'
          AND year BETWEEN 2021 AND 2025
        ORDER BY year, road_class
    """)
    for r in cur.fetchall():
        print(f"  {r[0]}  {r[1]:40s} {r[2]:>14,.1f} M km")

    print("\nSample: GB total all-motor-vehicle km 2021-2025 (TRA0201 All Motor Vehicles):")
    cur.execute("""
        SELECT year, vehicle_km_million FROM exposure_vehicle_km
        WHERE source_table='TRA0201' AND vehicle_type='All Motor Vehicles'
          AND year BETWEEN 2021 AND 2025 ORDER BY year
    """)
    for r in cur.fetchall():
        print(f"  {r[0]}  {r[1]:>14,.1f} M km")

    print("\nSample: licensed vehicles (UK, Total) 2021-2025:")
    cur.execute("""
        SELECT year, vehicles_thousand FROM exposure_licensed_vehicles
        WHERE geo_name='United Kingdom' AND vehicle_type='Total'
          AND year BETWEEN 2021 AND 2025 ORDER BY year
    """)
    for r in cur.fetchall():
        print(f"  {r[0]}  {r[1]:>14,.1f} thousand")

    cur.close()
    conn.close()
    print("\nDONE.")


if __name__ == "__main__":
    sys.exit(main())
