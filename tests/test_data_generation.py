import pandas as pd
import pytest

from routeready.data.generate import generate_inventory
from routeready.data.loader import load_inventory
from routeready.data.schema import COLUMNS, NON_NEGATIVE_COLUMNS


def test_generator_returns_expected_schema():
    df = generate_inventory()

    assert list(df.columns) == COLUMNS
    assert len(df) == 270


def test_generator_has_no_missing_or_negative_values():
    df = generate_inventory()

    assert not df.isnull().any().any()
    assert (df[NON_NEGATIVE_COLUMNS] >= 0).all().all()


def test_loader_reads_sample_dataset():
    df = load_inventory()

    assert len(df) == 270
    assert list(df.columns) == COLUMNS
    assert pd.api.types.is_datetime64_any_dtype(df["date"])


def test_loader_rejects_missing_columns(tmp_path):
    path = tmp_path / "invalid.csv"
    pd.DataFrame({"date": ["2026-01-01"]}).to_csv(path, index=False)

    with pytest.raises(ValueError, match="Missing required columns"):
        load_inventory(path)
