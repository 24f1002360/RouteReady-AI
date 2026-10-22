"""Generate deterministic synthetic inventory and demand data."""

import random
from pathlib import Path

import pandas as pd

from .schema import COLUMNS

REGIONS = ["North Demo", "East Demo", "South Demo"]
CATEGORIES = ["Medical", "Food", "Water"]


def generate_inventory(seed: int = 42) -> pd.DataFrame:
    """Generate 90 synthetic daily inventory records."""
    rng = random.Random(seed)
    rows = []

    for region in REGIONS:
        for category in CATEGORIES:
            stock = rng.randint(100, 500)
            lead_time = rng.randint(2, 10)

            for day in range(30):
                demand = rng.randint(10, 50)
                incoming = 100 if day in (10, 20) else 0
                date = (
                    pd.Timestamp("2026-09-21") + pd.Timedelta(days=day)
                ).date().isoformat()

                rows.append({
                    "date": date,
                    "demo_region": region,
                    "supply_category": category,
                    "daily_demand": demand,
                    "available_stock": stock,
                    "replenishment_lead_days": lead_time,
                    "incoming_quantity": incoming,
                    "scenario_id": (
                        "demand_surge"
                        if category == "Food" and day >= 20
                        else "baseline"
                    ),
                })

                stock = max(0, stock - demand + incoming)

    return pd.DataFrame(rows, columns=COLUMNS)


if __name__ == "__main__":
    output = Path(__file__).resolve().parents[3] / "data" / "sample" / "inventory.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    generate_inventory().to_csv(output, index=False)
    print(f"Created synthetic dataset: {output}")
