"""Load and validate RouteReady synthetic inventory data."""

from pathlib import Path
import pandas as pd

from routeready.data.schema import COLUMNS, NUMERIC_COLUMNS, NON_NEGATIVE_COLUMNS

DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parents[3]
    / "data" / "sample" / "inventory.csv"
)

TEXT_COLUMNS = ["demo_region", "supply_category", "scenario_id"]


def load_inventory(path=DEFAULT_DATA_PATH) -> pd.DataFrame:
    """Load and validate the inventory CSV."""
    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(f"Inventory dataset not found: {path}")

    try:
        df = pd.read_csv(path)
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise ValueError(f"Invalid inventory CSV: {exc}") from exc

    missing_columns = set(COLUMNS) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    df = df[COLUMNS].copy()

    if df.empty:
        raise ValueError("Inventory dataset is empty.")

    if df.isnull().any().any():
        raise ValueError("Inventory dataset contains missing values.")

    for column in TEXT_COLUMNS:
        df[column] = df[column].astype(str).str.strip()
        if df[column].eq("").any():
            raise ValueError(f"{column} cannot contain blank values.")

    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="raise")

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="raise")
        if not df[column].map(
            lambda value: float(value).is_integer()
        ).all():
            raise ValueError(f"{column} must contain whole numbers.")

    if (df[NON_NEGATIVE_COLUMNS] < 0).any().any():
        raise ValueError("Inventory numeric values cannot be negative.")

    if (df["replenishment_lead_days"] < 1).any():
        raise ValueError("Replenishment lead time must be at least one day.")

    if df.duplicated().any():
        raise ValueError("Inventory dataset contains duplicate rows.")

    return df
