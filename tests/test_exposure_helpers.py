"""
Unit tests for the pure parsing helpers in etl/load_exposure.py (Phase B).

These cover the ODS-reading helpers that do NOT need the spreadsheet
files themselves: year-name detection, unit conversion, and the two
"melt" orientations used to normalise wide DfT tables into long form.

Run with:

    python -m pytest tests/ -q
"""

import pandas as pd
import pytest

import load_exposure


# ------------------------------------------------------------------
# _is_year_name / _year_from_name
# ------------------------------------------------------------------
class TestIsYearName:
    def test_bare_year(self):
        assert load_exposure._is_year_name("2021") is True

    def test_year_with_note_suffix(self):
        # Real ODS header style: '2021 [note 3]'
        assert load_exposure._is_year_name("2021 [note 3]") is True

    def test_leading_whitespace(self):
        assert load_exposure._is_year_name("  2022") is True

    def test_non_year_name(self):
        assert load_exposure._is_year_name("Year") is False

    def test_out_of_range_high(self):
        assert load_exposure._is_year_name("2035") is False

    def test_out_of_range_low(self):
        assert load_exposure._is_year_name("1899") is False


class TestYearFromName:
    def test_bare_year(self):
        assert load_exposure._year_from_name("2021") == 2021

    def test_year_with_note_suffix(self):
        assert load_exposure._year_from_name("2021 [note 3]") == 2021

    def test_invalid_name_raises(self):
        with pytest.raises(ValueError):
            load_exposure._year_from_name("Year")


# ------------------------------------------------------------------
# _unit_factor
# ------------------------------------------------------------------
class TestUnitFactor:
    def test_billion_converted(self):
        df = pd.DataFrame({"Units": ["billion vehicle-km"]})
        assert load_exposure._unit_factor(df) == 1000.0

    def test_already_million(self):
        df = pd.DataFrame({"Units": ["million vehicle-km"]})
        assert load_exposure._unit_factor(df) == 1.0

    def test_missing_units_column(self):
        df = pd.DataFrame({"Year": [2021]})
        assert load_exposure._unit_factor(df) == 1.0

    def test_blank_units_value(self):
        df = pd.DataFrame({"Units": [None]})
        assert load_exposure._unit_factor(df) == 1.0


# ------------------------------------------------------------------
# _melt_wide_years (Orientation B: years are column names)
# ------------------------------------------------------------------
class TestMeltWideYears:
    def test_shape_and_values(self):
        df = pd.DataFrame({
            "Road Type": ["All", "All"],
            "2021": [1.0, 2.0],
            "2022 [note 1]": [3.0, 4.0],
        })
        out = load_exposure._melt_wide_years(df, ["Road Type"])
        assert len(out) == 4
        assert set(out.columns) == {"Road Type", "year", "value"}
        row = out[(out["Road Type"] == "All") & (out["year"] == 2022)].iloc[0]
        assert row["value"] == 3.0

    def test_missing_id_column_is_tolerated(self):
        # id_cols not present in the frame must be skipped, not raise
        df = pd.DataFrame({"2021": [5.0]})
        out = load_exposure._melt_wide_years(df, ["Not Present"])
        assert out["year"].tolist() == [2021]
        assert out["value"].tolist() == [5.0]

    def test_no_year_columns_yields_empty(self):
        df = pd.DataFrame({"Road Type": ["All"]})
        out = load_exposure._melt_wide_years(df, ["Road Type"])
        assert len(out) == 0


# ------------------------------------------------------------------
# _melt_metric_cols (Orientation A: year is a data column,
#                   metrics are the other columns)
# ------------------------------------------------------------------
class TestMeltMetricCols:
    def test_shape_and_values(self):
        df = pd.DataFrame({
            "Year": ["2021", "2022"],
            "All Motor Vehicles": [100.0, 110.0],
            "Cars": [80.0, 90.0],
        })
        out = load_exposure._melt_metric_cols(df, "Year", exclude=set())
        assert len(out) == 4
        assert set(out["metric"]) == {"All Motor Vehicles", "Cars"}
        row = out[out["metric"] == "Cars"].iloc[0]
        assert row["year"] == 2021 and row["value"] == 80.0

    def test_excluded_columns_dropped(self):
        df = pd.DataFrame({
            "Year": ["2021"],
            "Cars": [1.0],
            "Notes": ["x"],
            "Units": ["million"],
        })
        out = load_exposure._melt_metric_cols(
            df, "Year", exclude={"Notes", "Units"})
        assert out["metric"].tolist() == ["Cars"]

    def test_year_named_columns_never_treated_as_metrics(self):
        df = pd.DataFrame({
            "Year": ["2021"],
            "Cars": [1.0],
            "2021": [99.0],  # looks like a metric, but is a year column
        })
        out = load_exposure._melt_metric_cols(df, "Year", exclude=set())
        assert out["metric"].tolist() == ["Cars"]

    def test_numeric_year_values_coerced(self):
        df = pd.DataFrame({
            "Year": [2021, 2022],  # ints, not strings
            "Cars": [1.0, 2.0],
        })
        out = load_exposure._melt_metric_cols(df, "Year", exclude=set())
        assert out["year"].tolist() == [2021, 2022]
