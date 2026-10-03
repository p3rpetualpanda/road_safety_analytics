-- ============================================================
-- Road Safety Analytics — SQL Data Warehouse Schema
-- Target:  PostgreSQL 14+
-- Source:  DfT Road Safety Data (data.dft.gov.uk/road-accidents-safety-data)
-- Design:  Star schema — 3 facts + 2 dimensions
--
-- Grain:
--   fact_accident  = one accident
--   fact_casualty  = one casualty
--   fact_vehicle   = one vehicle
--
-- Idempotent: safe to re-run (drops + recreates).
-- ============================================================

-- Drop in reverse dependency order
DROP TABLE IF EXISTS fact_vehicle   CASCADE;
DROP TABLE IF EXISTS fact_casualty  CASCADE;
DROP TABLE IF EXISTS fact_accident  CASCADE;
DROP TABLE IF EXISTS dim_location   CASCADE;
DROP TABLE IF EXISTS dim_date       CASCADE;

-- ------------------------------------------------------------
-- dim_date: calendar dimension
-- ------------------------------------------------------------
CREATE TABLE dim_date (
    date_key         INT          PRIMARY KEY,   -- YYYYMMDD
    full_date        DATE         NOT NULL,
    year             INT          NOT NULL,
    month            INT          NOT NULL,
    month_name       TEXT         NOT NULL,
    quarter          INT          NOT NULL,
    day_of_week      INT          NOT NULL,      -- 1=Mon .. 7=Sun
    day_of_week_name TEXT         NOT NULL,
    is_weekend       BOOLEAN      NOT NULL
);

-- ------------------------------------------------------------
-- dim_location: geographic / road dimension
-- One row per unique (district, road_class, urban_rural,
-- police_force, lat, long) combination.
-- ------------------------------------------------------------
CREATE TABLE dim_location (
    location_key     INT          PRIMARY KEY,
    district         TEXT,
    road_class       TEXT,
    urban_rural      TEXT,
    police_force     TEXT,
    lat              NUMERIC(9,6),
    long             NUMERIC(9,6)
);

-- ------------------------------------------------------------
-- fact_accident: grain = one accident
-- ------------------------------------------------------------
CREATE TABLE fact_accident (
    accident_index   TEXT         PRIMARY KEY,
    date_key         INT          NOT NULL REFERENCES dim_date(date_key),
    location_key     INT          NOT NULL REFERENCES dim_location(location_key),
    accident_time    TIME,
    severity         SMALLINT     NOT NULL CHECK (severity IN (1,2,3)),
    weather          TEXT,
    lighting         TEXT,
    road_surface     TEXT,
    num_vehicles     INT,
    num_casualties   INT,
    speed_limit      INT          -- mph; now sourced from the accidents table
);

-- ------------------------------------------------------------
-- fact_casualty: grain = one casualty
-- Denormalises date_key + location_key from the parent accident
-- so Power BI can slice casualties directly by date/location
-- without a triple join.
-- ------------------------------------------------------------
CREATE TABLE fact_casualty (
    casualty_rec     TEXT         PRIMARY KEY,
    accident_index   TEXT         NOT NULL REFERENCES fact_accident(accident_index),
    date_key         INT          NOT NULL REFERENCES dim_date(date_key),
    location_key     INT          NOT NULL REFERENCES dim_location(location_key),
    age              INT,
    age_band         TEXT,
    sex              TEXT,
    casualty_type    TEXT,
    severity         SMALLINT     NOT NULL CHECK (severity IN (1,2,3)),
    vru_flag         BOOLEAN      NOT NULL       -- vulnerable road user
);

-- ------------------------------------------------------------
-- fact_vehicle: grain = one vehicle
-- ------------------------------------------------------------
CREATE TABLE fact_vehicle (
    vehicle_rec      TEXT         PRIMARY KEY,
    accident_index   TEXT         NOT NULL REFERENCES fact_accident(accident_index),
    vehicle_type     TEXT,
    manoeuvre        TEXT,
    engine_size_cc   INT,
    propellant       TEXT,
    driver_age_band  TEXT,
    driver_sex       TEXT
);

-- ------------------------------------------------------------
-- Indexes for common analytical patterns
-- ------------------------------------------------------------
CREATE INDEX idx_fact_accident_date      ON fact_accident(date_key);
CREATE INDEX idx_fact_accident_location  ON fact_accident(location_key);
CREATE INDEX idx_fact_accident_severity  ON fact_accident(severity);
CREATE INDEX idx_fact_casualty_date      ON fact_casualty(date_key);
CREATE INDEX idx_fact_casualty_location  ON fact_casualty(location_key);
CREATE INDEX idx_fact_casualty_severity  ON fact_casualty(severity);
CREATE INDEX idx_fact_casualty_vru       ON fact_casualty(vru_flag);
CREATE INDEX idx_fact_vehicle_accident   ON fact_vehicle(accident_index);
CREATE INDEX idx_fact_vehicle_type       ON fact_vehicle(vehicle_type);
