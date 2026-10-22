"""Shared schema for synthetic inventory and demand data."""

COLUMNS = [
    "date",
    "demo_region",
    "supply_category",
    "daily_demand",
    "available_stock",
    "replenishment_lead_days",
    "incoming_quantity",
    "scenario_id",
]

NUMERIC_COLUMNS = [
    "daily_demand",
    "available_stock",
    "replenishment_lead_days",
    "incoming_quantity",
]

NON_NEGATIVE_COLUMNS = [
    "daily_demand",
    "available_stock",
    "replenishment_lead_days",
    "incoming_quantity",
]
