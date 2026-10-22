# Data

All data in this folder is synthetic demonstration data. It contains no
real operational or private records.

## Files

- `sample/inventory.csv`: 270 daily synthetic records.
- Scenarios: `baseline` and `demand_surge`.

## Schema

| Column | Type | Rule | Meaning |
|---|---|---|---|
| date | Date | Valid date | Day of the record |
| demo_region | Text | Non-empty | Demo region: North Demo, East Demo, South Demo |
| supply_category | Text | Non-empty | Category: Medical, Food, Water |
| daily_demand | Integer | >= 0 | Units demanded that day |
| available_stock | Integer | >= 0 | Units in stock that day |
| replenishment_lead_days | Integer | >= 1 | Days until replenishment arrives |
| incoming_quantity | Integer | >= 0 | Units arriving that day |
| scenario_id | Text | Non-empty | `baseline` or `demand_surge` |

## Regenerate the dataset

    PYTHONPATH=src python -m routeready.data.generate

## Load the dataset

    from routeready.data import load_inventory

    df = load_inventory()
    df = load_inventory("path/to/file.csv")

The loader validates required columns, missing values, dates, numeric
values, non-empty text fields, replenishment lead times, and duplicate rows.

## Run tests

    PYTHONPATH=src pytest -q
