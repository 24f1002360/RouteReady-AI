import pandas as pd
import pytest

from routeready.data.generate import generate_inventory
from routeready.data.loader import load_inventory


def write(tmp_path, df, name="inventory.csv"):
    path = tmp_path / name
    df.to_csv(path, index=False)
    return path


def valid_df():
    df = generate_inventory().copy()
    df["date"] = df["date"].astype(str)
    return df


def test_valid_file_loads(tmp_path):
    assert len(load_inventory(write(tmp_path, valid_df()))) == 270


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_inventory(tmp_path / "missing.csv")


def test_empty_file(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("")
    with pytest.raises(ValueError):
        load_inventory(path)


def test_header_only_file(tmp_path):
    with pytest.raises(ValueError):
        load_inventory(write(tmp_path, valid_df().iloc[0:0]))


def test_negative_stock(tmp_path):
    df = valid_df()
    df.loc[0, "available_stock"] = -5
    with pytest.raises(ValueError):
        load_inventory(write(tmp_path, df))


def test_non_numeric_demand(tmp_path):
    df = valid_df()
    df["daily_demand"] = df["daily_demand"].astype(object)
    df.loc[0, "daily_demand"] = "abc"
    with pytest.raises(ValueError):
        load_inventory(write(tmp_path, df))


def test_missing_value(tmp_path):
    df = valid_df()
    df.loc[0, "daily_demand"] = None
    with pytest.raises(ValueError):
        load_inventory(write(tmp_path, df))


def test_fractional_lead_days(tmp_path):
    df = valid_df()
    df["replenishment_lead_days"] = df["replenishment_lead_days"].astype(float)
    df.loc[0, "replenishment_lead_days"] = 2.5
    with pytest.raises(ValueError):
        load_inventory(write(tmp_path, df))


def test_zero_lead_days(tmp_path):
    df = valid_df()
    df.loc[0, "replenishment_lead_days"] = 0
    with pytest.raises(ValueError):
        load_inventory(write(tmp_path, df))


def test_invalid_date(tmp_path):
    df = valid_df()
    df.loc[0, "date"] = "not-a-date"
    with pytest.raises(ValueError):
        load_inventory(write(tmp_path, df))


def test_blank_category(tmp_path):
    df = valid_df()
    df.loc[0, "supply_category"] = ""
    with pytest.raises(ValueError):
        load_inventory(write(tmp_path, df))


def test_duplicate_rows(tmp_path):
    df = pd.concat([valid_df(), valid_df().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError):
        load_inventory(write(tmp_path, df))
