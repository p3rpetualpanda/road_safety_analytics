"""
Unit tests for the pure cleaning/transform functions in etl/load.py.

These functions are the heart of the data-quality layer, so they are
tested in isolation (no database required). Run with:

    python -m pytest tests/ -q
"""

import pandas as pd

import load


# ------------------------------------------------------------------
# clean_severity
# ------------------------------------------------------------------
class TestCleanSeverity:
    def test_keeps_valid_codes(self):
        out = load.clean_severity(pd.Series([1, 2, 3]))
        assert out.tolist() == [1, 2, 3]

    def test_drops_invalid_codes(self):
        out = load.clean_severity(pd.Series([0, 4, 99]))
        assert out.isna().all()

    def test_coerces_non_numeric(self):
        out = load.clean_severity(pd.Series(["2", "x", None]))
        assert out.iloc[0] == 2
        assert pd.isna(out.iloc[1])
        assert pd.isna(out.iloc[2])


# ------------------------------------------------------------------
# clean_age
# ------------------------------------------------------------------
class TestCleanAge:
    def test_maps_unknown_code_to_null(self):
        out = load.clean_age(pd.Series([-1]))
        assert out.isna().all()

    def test_keeps_real_ages(self):
        # 0 = under one year old in STATS19; only -1 means unknown
        out = load.clean_age(pd.Series([0, 1, 25, 80, 99]))
        assert out.tolist() == [0, 1, 25, 80, 99]

    def test_mixed(self):
        out = load.clean_age(pd.Series([25, 99, "40", None, 0, -1]))
        assert out.iloc[0] == 25
        assert out.iloc[1] == 99
        assert out.iloc[2] == 40
        assert pd.isna(out.iloc[3])
        assert out.iloc[4] == 0
        assert pd.isna(out.iloc[5])


# ------------------------------------------------------------------
# age_band
# ------------------------------------------------------------------
class TestAgeBand:
    def test_standard_band(self):
        out = load.age_band(pd.Series([25]))
        assert out.iloc[0] == "25-29"

    def test_band_boundaries(self):
        out = load.age_band(pd.Series([0, 5, 9, 10]))
        assert out.iloc[0] == "0-4"
        assert out.iloc[1] == "5-9"
        assert out.iloc[2] == "5-9"
        assert out.iloc[3] == "10-14"

    def test_missing_is_unknown(self):
        out = load.age_band(pd.Series([pd.NA]))
        assert out.iloc[0] == "Unknown"


# ------------------------------------------------------------------
# clean_time
# ------------------------------------------------------------------
class TestCleanTime:
    # --- New DfT spec: "HH:MM" ---
    def test_new_spec_hhmm(self):
        out = load.clean_time(pd.Series(["08:30"]))
        assert out.iloc[0] == "08:30:00"

    def test_new_spec_with_seconds(self):
        out = load.clean_time(pd.Series(["15:00:45"]))
        assert out.iloc[0] == "15:00:45"

    def test_new_spec_midnight(self):
        out = load.clean_time(pd.Series(["00:00"]))
        assert out.iloc[0] == "00:00:00"

    def test_new_spec_last_minute(self):
        out = load.clean_time(pd.Series(["23:59"]))
        assert out.iloc[0] == "23:59:00"

    def test_new_spec_invalid_hour(self):
        out = load.clean_time(pd.Series(["24:00"]))
        assert out.iloc[0] is None

    def test_new_spec_invalid_minute(self):
        out = load.clean_time(pd.Series(["12:60"]))
        assert out.iloc[0] is None

    # --- Legacy: "HHMM" ---
    def test_legacy_hhmm(self):
        out = load.clean_time(pd.Series(["0830"]))
        assert out.iloc[0] == "08:30:00"

    def test_legacy_pads_short_values(self):
        out = load.clean_time(pd.Series(["830"]))
        assert out.iloc[0] == "08:30:00"

    def test_legacy_midnight_and_last_minute(self):
        out = load.clean_time(pd.Series(["0000", "2359"]))
        assert out.iloc[0] == "00:00:00"
        assert out.iloc[1] == "23:59:00"

    def test_legacy_invalid_hour(self):
        out = load.clean_time(pd.Series(["2400"]))
        assert out.iloc[0] is None

    def test_legacy_invalid_minute(self):
        out = load.clean_time(pd.Series(["1260"]))
        assert out.iloc[0] is None

    def test_non_numeric(self):
        out = load.clean_time(pd.Series(["abcd"]))
        assert out.iloc[0] is None

    def test_missing(self):
        out = load.clean_time(pd.Series([None]))
        assert out.iloc[0] is None


# ------------------------------------------------------------------
# clean_coord
# ------------------------------------------------------------------
class TestCleanCoord:
    def test_keeps_in_range(self):
        out = load.clean_coord(pd.Series([51.5, -0.12]), -90, 90)
        assert out.tolist() == [51.5, -0.12]

    def test_drops_out_of_range(self):
        out = load.clean_coord(pd.Series([95, -95]), -90, 90)
        assert out.isna().all()

    def test_coerces_non_numeric(self):
        out = load.clean_coord(pd.Series(["abc"]), -90, 90)
        assert out.isna().all()


# ------------------------------------------------------------------
# is_vru
# ------------------------------------------------------------------
class TestIsVru:
    """is_vru now keys off casualty_type: 0 (pedestrian) and 1 (cyclist) are VRU."""

    def test_flags_pedestrian_and_cyclist(self):
        out = load.is_vru(pd.Series([0, 1]))
        assert out.tolist() == [True, True]

    def test_does_not_flag_motorist(self):
        out = load.is_vru(pd.Series([9, 19, 21]))
        assert out.tolist() == [False, False, False]

    def test_string_codes(self):
        out = load.is_vru(pd.Series(["0", "1", "9"]))
        assert out.tolist() == [True, True, False]

    def test_missing_is_false(self):
        out = load.is_vru(pd.Series([None]))
        assert out.tolist() == [False]

    def test_unknown_code(self):
        out = load.is_vru(pd.Series([-1]))
        assert out.tolist() == [False]


# ------------------------------------------------------------------
# decode_code / df_to_rows
# ------------------------------------------------------------------
class TestDecodeCode:
    def test_maps_known_codes(self):
        out = load.decode_code(pd.Series([1, 2, 3]), {1: "A", 2: "B", 3: "C"})
        assert out.tolist() == ["A", "B", "C"]

    def test_unmapped_becomes_unknown(self):
        out = load.decode_code(pd.Series([1, 99]), {1: "A"})
        assert out.iloc[0] == "A"
        assert out.iloc[1] == "Unknown"

    def test_non_numeric_becomes_unknown(self):
        out = load.decode_code(pd.Series(["abc", None]), {1: "A"})
        assert out.iloc[0] == "Unknown"
        assert out.iloc[1] == "Unknown"

    def test_negative_codes(self):
        out = load.decode_code(pd.Series([-1, 1]), {-1: "Unknown", 1: "A"})
        assert out.iloc[0] == "Unknown"
        assert out.iloc[1] == "A"


class TestDfToRows:
    def test_maps_nan_to_none(self):
        df = pd.DataFrame({"a": [1, None], "b": ["x", "y"]})
        rows = load.df_to_rows(df)
        assert rows[0] == {"a": 1, "b": "x"}
        assert rows[1] == {"a": None, "b": "y"}

    def test_empty_dataframe(self):
        df = pd.DataFrame({"a": pd.Series(dtype="Int64")})
        assert load.df_to_rows(df) == []


# ------------------------------------------------------------------
# Code tables: pinned to the DfT STATS19 code list (a past mapping
# mislabelled rain as "Fine with precipitation" and fog as "Rain").
# ------------------------------------------------------------------
class TestCodeTables:
    def test_weather(self):
        assert load.WEATHER_CONDITIONS[2] == "Raining no high winds"
        assert load.WEATHER_CONDITIONS[4] == "Fine + high winds"
        assert load.WEATHER_CONDITIONS[7] == "Fog or mist"

    def test_light_and_surface(self):
        assert load.LIGHT_CONDITIONS[7] == "Darkness - lighting unknown"
        assert load.ROAD_SURFACE_CONDITIONS[4] == "Frost or ice"
        assert load.ROAD_SURFACE_CONDITIONS[5] == "Flood over 3cm deep"

    def test_road_class(self):
        assert [load.FIRST_ROAD_CLASS[k] for k in range(1, 7)] == ["Motorway", "A(M)", "A", "B", "C", "Unclassified"]
