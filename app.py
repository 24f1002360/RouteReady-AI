"""RouteReady AI integrated dashboard — Person 4 starter.

Uses synthetic, non-operational inventory data and Person 3's existing TinyFish client.
Public signals only affect a category's heuristic score when a source publication date
is explicitly supplied, fresh (within 7 days), category-matched, and fetched successfully.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd
import streamlit as st

from routeready.config import Settings
from routeready.tinyfish import TinyFishClient, TinyFishError, normalize_signal

DATA_PATH = ROOT / "data" / "synthetic_demand_inventory.csv"
FORECAST_WINDOW_DAYS = 7
SIGNAL_FRESHNESS_DAYS = 7

# Deliberately generic demo categories; all values are synthetic.
DEMO_INVENTORY = {
    "Packaging": {"base_demand": 18, "available_stock": 95, "incoming_quantity": 40, "lead_time_days": 6},
    "Labels": {"base_demand": 12, "available_stock": 40, "incoming_quantity": 0, "lead_time_days": 5},
    "Hygiene Kits": {"base_demand": 10, "available_stock": 140, "incoming_quantity": 60, "lead_time_days": 8},
    "Protective Gear": {"base_demand": 15, "available_stock": 55, "incoming_quantity": 20, "lead_time_days": 7},
}

CATEGORY_TERMS = {
    "Packaging": ("packaging", "carton", "cardboard box", "corrugated box", "packaging material"),
    "Labels": ("label", "labels", "labeling", "labelling", "adhesive label", "printing label"),
    "Hygiene Kits": ("hygiene kit", "hygiene supplies", "soap", "sanitizer", "sanitiser", "sanitary supplies"),
    "Protective Gear": ("protective gear", "protective equipment", "personal protective equipment", "ppe", "gloves", "respirator"),
}


def build_synthetic_history(days: int = 28) -> pd.DataFrame:
    """Create deterministic, visibly synthetic daily demand/history rows."""
    today = pd.Timestamp.now(tz=None).normalize()
    dates = pd.date_range(end=today, periods=days, freq="D")
    rows: list[dict[str, Any]] = []
    for category_index, (category, settings) in enumerate(DEMO_INVENTORY.items()):
        # Small, deterministic oscillation means the forecast is repeatable and testable.
        for day_index, day in enumerate(dates):
            swing = ((day_index * 3 + category_index * 2) % 7) - 3
            demand = max(1, int(settings["base_demand"] + swing))
            rows.append({
                "date": day.date().isoformat(),
                "category": category,
                "demand": demand,
                "available_stock": settings["available_stock"],
                "incoming_quantity": settings["incoming_quantity"],
                "lead_time_days": settings["lead_time_days"],
            })
    return pd.DataFrame(rows)


def load_inventory() -> tuple[pd.DataFrame, list[str]]:
    """Load the bundled CSV; create it once from labeled synthetic values if absent."""
    messages: list[str] = []
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        build_synthetic_history().to_csv(DATA_PATH, index=False)
        messages.append("The synthetic CSV was missing, so a new demo dataset was created at data/synthetic_demand_inventory.csv.")

    try:
        frame = pd.read_csv(DATA_PATH)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        return pd.DataFrame(), [f"Could not read {DATA_PATH.name}: {exc}"]

    required = {"date", "category", "demand", "available_stock", "incoming_quantity", "lead_time_days"}
    missing = sorted(required - set(frame.columns))
    if missing:
        return pd.DataFrame(), ["Missing required column(s): " + ", ".join(missing)]
    if frame.empty:
        return pd.DataFrame(), ["The synthetic inventory CSV contains no rows."]

    frame = frame.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    if frame["date"].isna().any():
        messages.append("Some date values are empty or invalid.")
    frame["category"] = frame["category"].astype("string").str.strip()
    if frame["category"].isna().any() or frame["category"].eq("").any():
        messages.append("Some category values are empty.")
    for column in ("demand", "available_stock", "incoming_quantity", "lead_time_days"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if frame[column].isna().any():
            messages.append(f"Column '{column}' contains missing or non-numeric values.")