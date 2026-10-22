"""RouteReady AI — Person 4 integrated Streamlit dashboard.

Uses synthetic, non-operational inventory data.
Public signals are evidence candidates that require human review.
Risk scores are heuristic priorities, not calibrated probabilities.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

# Make the src directory importable when Streamlit runs this root-level file.
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd
import streamlit as st

from routeready.config import Settings
from routeready.tinyfish import (
    TinyFishClient,
    TinyFishError,
    normalize_signal,
)


DATA_PATH = ROOT / "data" / "synthetic_demand_inventory.csv"
FORECAST_WINDOW_DAYS = 7
SIGNAL_FRESHNESS_DAYS = 7

# Synthetic examples only. These are not operational inventory records.
DEMO_INVENTORY = {
    "Packaging": {
        "base_demand": 18,
        "available_stock": 95,
        "incoming_quantity": 40,
        "lead_time_days": 6,
    },
    "Labels": {
        "base_demand": 12,
        "available_stock": 40,
        "incoming_quantity": 0,
        "lead_time_days": 5,
    },
    "Hygiene Kits": {
        "base_demand": 10,
        "available_stock": 140,
        "incoming_quantity": 60,
        "lead_time_days": 8,
    },
    "Protective Gear": {
        "base_demand": 15,
        "available_stock": 55,
        "incoming_quantity": 20,
        "lead_time_days": 7,
    },
}

CATEGORY_TERMS = {
    "Packaging": (
        "packaging",
        "carton",
        "cardboard box",
        "corrugated box",
        "packaging material",
    ),
    "Labels": (
        "label",
        "labels",
        "labeling",
        "labelling",
        "adhesive label",
        "printing label",
    ),
    "Hygiene Kits": (
        "hygiene kit",
        "hygiene supplies",
        "soap",
        "sanitizer",
        "sanitiser",
        "sanitary supplies",
    ),
    "Protective Gear": (
        "protective gear",
        "protective equipment",
        "personal protective equipment",
        "ppe",
        "gloves",
        "respirator",
    ),
}


def build_synthetic_history(days: int = 28) -> pd.DataFrame:
    """Build deterministic synthetic daily demand records."""
    today = pd.Timestamp.now(tz=None).normalize()
    dates = pd.date_range(end=today, periods=days, freq="D")
    rows: list[dict[str, Any]] = []

    for category_index, (category, config) in enumerate(
        DEMO_INVENTORY.items()
    ):
        for day_index, day in enumerate(dates):
            swing = ((day_index * 3 + category_index * 2) % 7) - 3
            demand = max(1, int(config["base_demand"] + swing))

            rows.append(
                {
                    "date": day.date().isoformat(),
                    "category": category,
                    "demand": demand,
                    "available_stock": config["available_stock"],
                    "incoming_quantity": config["incoming_quantity"],
                    "lead_time_days": config["lead_time_days"],
                }
            )

    return pd.DataFrame(rows)


def load_inventory() -> tuple[pd.DataFrame, list[str]]:
    """Load and validate synthetic inventory data."""
    messages: list[str] = []
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not DATA_PATH.exists():
        build_synthetic_history().to_csv(DATA_PATH, index=False)
        messages.append(
            "A synthetic demo dataset was created at "
            "data/synthetic_demand_inventory.csv."
        )

    try:
        frame = pd.read_csv(DATA_PATH)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        return pd.DataFrame(), [
            f"Could not read {DATA_PATH.name}: {exc}"
        ]

    required = {
        "date",
        "category",
        "demand",
        "available_stock",
        "incoming_quantity",
        "lead_time_days",
    }

    missing = sorted(required - set(frame.columns))
    if missing:
        return pd.DataFrame(), [
            "Missing required columns: " + ", ".join(missing)
        ]

    if frame.empty:
        return pd.DataFrame(), [
            "The synthetic inventory CSV contains no rows."
        ]

    frame = frame.copy()
    frame["date"] = pd.to_datetime(
        frame["date"], errors="coerce"
    )
    frame["category"] = frame["category"].astype("string").str.strip()

    if frame["date"].isna().any():
        messages.append("Some dates are missing or invalid.")

    if frame["category"].isna().any() or frame["category"].eq("").any():
        messages.append("Some category values are missing.")

    for column in (
        "demand",
        "available_stock",
        "incoming_quantity",
        "lead_time_days",
    ):
        frame[column] = pd.to_numeric(
            frame[column], errors="coerce"
        )

        if frame[column].isna().any():
            messages.append(
                f"Column '{column}' contains missing or non-numeric values."
            )
        elif (frame[column] < 0).any():
            messages.append(
                f"Column '{column}' contains negative values."
            )

    if frame.duplicated(subset=["date", "category"]).any():
        messages.append("Duplicate date/category rows were found.")

    return frame, messages


def publication_date_from_search(
    search_result: dict[str, Any],
) -> str | None:
    """Extract an explicit source publication date, if supplied."""
    date_keys = (
        "published_at",
        "publishedAt",
        "publication_date",
        "published_date",
        "date_published",
        "datePublished",
        "published",
        "date",
        "timestamp",
    )

    for key in date_keys:
        raw = search_result.get(key)

        if raw is None or raw == "":
            continue

        try:
            if isinstance(raw, (int, float)) and raw > 1_000_000_000:
                parsed = pd.to_datetime(
                    raw, unit="s", utc=True, errors="coerce"
                )
            else:
                parsed = pd.to_datetime(
                    raw, utc=True, errors="coerce"
                )

            if not pd.isna(parsed):
                return parsed.isoformat()

        except (TypeError, ValueError, OverflowError):
            continue

    return None


def refresh_tinyfish_signals(
    client: TinyFishClient,
    query: str,
) -> list[dict[str, Any]]:
    """Make real Search and Fetch requests using Person 3's client."""
    results = client.search(query)
    signals: list[dict[str, Any]] = []

    for result in results:
        published_at = publication_date_from_search(result)
        source_url = (
            result.get("url")
            or result.get("link")
            or result.get("source_url")
            or ""
        )

        try:
            if not source_url:
                signal = normalize_signal(result, None)
                signal["fetch_status"] = "failed"
                signal["status_note"] = (
                    "Search result did not contain a usable source URL."
                )
            else:
                payload = client.fetch(source_url)
                signal = normalize_signal(result, payload)

                if signal.get("fetched_content"):
                    signal["fetch_status"] = "fetched"
                    signal["status_note"] = (
                        "Fetched page text is available. "
                        "A human must verify relevance and context."
                    )
                else:
                    signal["fetch_status"] = "no_content"
                    signal["status_note"] = (
                        "Fetch returned no usable page text. "
                        "The Search snippet is not treated as fetched evidence."
                    )

        except TinyFishError as exc:
            signal = normalize_signal(result, None)
            signal["fetch_status"] = "failed"
            signal["status_note"] = f"Fetch failed: {exc}"

        except Exception as exc:
            signal = normalize_signal(result, None)
            signal["fetch_status"] = "failed"
            signal["status_note"] = (
                f"Fetch failed unexpectedly ({type(exc).__name__})."
            )

        signal["published_at"] = published_at
        signals.append(signal)

    return signals


def parse_timestamp(value: Any) -> pd.Timestamp | None:
    """Parse a timestamp without substituting retrieval time."""
    if not value:
        return None

    parsed = pd.to_datetime(value, utc=True, errors="coerce")
    return None if pd.isna(parsed) else parsed


def evaluate_signals_for_category(
    signals: list[dict[str, Any]],
    category: str,
) -> list[dict[str, Any]]:
    """Check category relevance, publication freshness, and fetch status."""
    checks: list[dict[str, Any]] = []
    now = pd.Timestamp.now(tz="UTC")
    terms = CATEGORY_TERMS.get(category, (category.lower(),))

    for signal in signals:
        title = str(signal.get("source_title") or "")
        snippet = str(signal.get("search_snippet") or "")
        excerpt = str(signal.get("evidence_excerpt") or "")

        combined_text = f"{title} {snippet} {excerpt}".lower()
        relevant = any(term in combined_text for term in terms)

        publication = parse_timestamp(signal.get("published_at"))

        if publication is None:
            fresh = False
            freshness_reason = (
                "Search did not provide a usable publication date. "
                "Retrieval time is not a publication date."
            )
        else:
            age = now - publication
            fresh = (
                pd.Timedelta(0)
                <= age
                <= pd.Timedelta(days=SIGNAL_FRESHNESS_DAYS)
            )

            if age < pd.Timedelta(0):
                freshness_reason = (
                    "Publication date is in the future."
                )
            elif age > pd.Timedelta(days=SIGNAL_FRESHNESS_DAYS):
                freshness_reason = (
                    f"Publication is older than {SIGNAL_FRESHNESS_DAYS} days."
                )
            else:
                freshness_reason = (
                    f"Publication is within the last "
                    f"{SIGNAL_FRESHNESS_DAYS} days."
                )

        fetched = (
            signal.get("fetch_status") == "fetched"
            and bool(signal.get("fetched_content"))
        )

        reasons = []

        if not relevant:
            reasons.append("No explicit category keyword match")

        if not fresh:
            reasons.append(freshness_reason)

        if not fetched:
            reasons.append("Fetch did not return usable page text")

        eligible = relevant and fresh and fetched

        if eligible:
            reason = (
                "The signal passed the category-match, publication-freshness, "
                "and fetched-content checks."
            )
        else:
            reason = "; ".join(reasons)

        checks.append(
            {
                "source_title": title or "Untitled public source",
                "source_url": signal.get("source_url") or "",
                "relevant": relevant,
                "fresh": fresh,
                "fetched": fetched,
                "eligible": eligible,
                "reason": reason,
                "published_at": signal.get("published_at"),
            }
        )

    return checks


def make_forecast_and_risk(
    history: pd.DataFrame,
    horizon_days: int,
    signals: list[dict[str, Any]],
) -> pd.DataFrame:
    """Calculate moving-average demand and explainable heuristic risk."""
    rows: list[dict[str, Any]] = []

    for category, group in history.sort_values("date").groupby(
        "category", sort=True
    ):
        recent = group.tail(FORECAST_WINDOW_DAYS)

        avg_daily = float(recent["demand"].mean())
        last = group.iloc[-1]

        stock = float(last["available_stock"])
        incoming = float(last["incoming_quantity"])
        lead_days = float(last["lead_time_days"])

        coverage = stock / avg_daily if avg_daily > 0 else 0.0
        lead_demand = avg_daily * lead_days

        variability = (
            float(recent["demand"].std(ddof=0) / avg_daily)
            if avg_daily > 0
            else 0.0
        )

        if coverage <= lead_days:
            coverage_points = 40
        elif coverage < lead_days + 3:
            coverage_points = 30
        elif coverage < lead_days + 7:
            coverage_points = 20
        elif coverage < lead_days + 14:
            coverage_points = 10
        else:
            coverage_points = 0

        lead_points = min(
            25, max(0, round((lead_days - 2) * 3))
        )

        if variability >= 0.40:
            variability_points = 15
        elif variability >= 0.25:
            variability_points = 10
        elif variability >= 0.15:
            variability_points = 5
        else:
            variability_points = 0

        # Incoming stock has no ETA, so it is not counted as confirmed supply.
        replenishment_points = 10 if incoming <= 0 else 5

        checks = evaluate_signals_for_category(
            signals, str(category)
        )
        eligible_checks = [
            item for item in checks if item["eligible"]
        ]

        # At most one public-signal bonus is applied per category.
        signal_points = 10 if eligible_checks else 0

        components = {
            "Stock coverage pressure": int(coverage_points),
            "Supplier lead-time pressure": int(lead_points),
            "Demand variability": int(variability_points),
            "Replenishment uncertainty": int(replenishment_points),
            "Fresh, relevant fetched signal": int(signal_points),
        }

        score = min(100, sum(components.values()))

        if score >= 70:
            level = "High"
        elif score >= 40:
            level = "Moderate"
        else:
            level = "Low"

        reasons = [
            (
                f"Stock covers approximately {coverage:.1f} days against "
                f"a {lead_days:.1f}-day supplier lead time "
                f"({coverage_points}/40 points)."
            ),
            (
                f"Supplier lead time is {lead_days:.1f} days "
                f"({lead_points}/25 points)."
            ),
            (
                f"Recent demand coefficient of variation is "
                f"{variability:.2f} ({variability_points}/15 points)."
            ),
        ]

        if incoming > 0:
            reasons.append(
                f"{incoming:g} incoming units have no arrival date. "
                f"They are not treated as confirmed near-term supply "
                f"({replenishment_points}/10 points)."
            )
        else:
            reasons.append(
                "No incoming quantity is recorded "
                f"({replenishment_points}/10 points)."
            )

        if eligible_checks:
            reasons.append(
                "A fresh, category-matched signal with fetched text "
                f"adds +10 points. The bonus is capped at 10; "
                f"{len(eligible_checks)} source(s) passed the checks."
            )
        elif checks:
            reasons.append(
                "Public signals add +0 points because none passed "
                "all relevance, freshness, and fetched-content checks."
            )
        else:
            reasons.append(
                "No public signals were retrieved; this score uses "
                "inventory-only inputs."
            )

        rows.append(
            {
                "Category": str(category),
                "Average demand/day": round(avg_daily, 2),
                "Forecast horizon (days)": int(horizon_days),
                "Forecast demand": round(avg_daily * horizon_days, 1),
                "Available stock": round(stock, 1),
                "Incoming quantity (undated)": round(incoming, 1),
                "Stock coverage (days)": round(coverage, 1),
                "Supplier lead time (days)": round(lead_days, 1),
                "Demand during lead time": round(lead_demand, 1),
                "Demand variability (CV)": round(variability, 2),
                "Risk score (heuristic)": int(score),
                "Risk level": level,
                "components": components,
                "reasons": reasons,
                "signal_checks": checks,
            }
        )

    return pd.DataFrame(rows)


# ---------------- Streamlit dashboard ----------------

st.set_page_config(
    page_title="RouteReady AI | Inventory & Risk Review",
    page_icon=":compass:",
    layout="wide",
)

st.title("RouteReady AI")
st.caption(
    "Synthetic inventory → demand baseline → stock coverage → "
    "public evidence → explainable human review"
)

st.info(
    "**Synthetic demo data.** This is a non-operational prototype. "
    "Risk scores are heuristic priorities, not calibrated probabilities. "
    "Public signals are evidence candidates and require human review."
)

# Keep results in session state so normal reruns do not call live APIs.
if "rr_signals" not in st.session_state:
    st.session_state.rr_signals = []

if "rr_last_refresh_at" not in st.session_state:
    st.session_state.rr_last_refresh_at = ""

if "rr_last_refresh_status" not in st.session_state:
    st.session_state.rr_last_refresh_status = "never"

if "rr_last_refresh_error" not in st.session_state:
    st.session_state.rr_last_refresh_error = ""

settings = Settings.from_env()

with st.sidebar:
    st.header("Dashboard controls")

    horizon_days = st.slider(
        "Forecast horizon (days)",
        min_value=3,
        max_value=14,
        value=7,
    )

    query = st.text_input(
        "Generic public-information query",
        value="public news packaging materials supply disruption",
        help=(
            "Use generic public queries only. Do not enter sensitive routes, "
            "locations, movements, or private information."
        ),
    )

    if settings.tinyfish_api_key:
        st.success("TinyFish API key configured")
    else:
        st.warning(
            "TinyFish key missing — inventory-only mode is available."
        )

    st.caption(
        "TinyFish is called only when you press the refresh button."
    )

    refresh_clicked = st.button(
        "Refresh public signals",
        type="primary",
        use_container_width=True,
    )

# This is the only section that triggers live API requests.
if refresh_clicked:
    if not settings.tinyfish_api_key:
        st.session_state.rr_last_refresh_status = "failed"
        st.session_state.rr_last_refresh_error = (
            "TINYFISH_API_KEY is missing. Add it to your local .env file."
        )

    elif not query.strip():
        st.session_state.rr_last_refresh_status = "failed"
        st.session_state.rr_last_refresh_error = (
            "Enter a public-information query before refreshing."
        )

    else:
        try:
            with st.spinner("Calling TinyFish Search and Fetch..."):
                signals_now = refresh_tinyfish_signals(
                    TinyFishClient(settings),
                    query.strip(),
                )

            st.session_state.rr_signals = signals_now
            st.session_state.rr_last_refresh_at = (
                datetime.now(timezone.utc).isoformat(timespec="seconds")
            )
            st.session_state.rr_last_refresh_status = "success"
            st.session_state.rr_last_refresh_error = ""

        except TinyFishError as exc:
            st.session_state.rr_last_refresh_status = "failed"
            st.session_state.rr_last_refresh_error = str(exc)

        except Exception as exc:
            st.session_state.rr_last_refresh_status = "failed"
            st.session_state.rr_last_refresh_error = (
                f"Unexpected {type(exc).__name__}; "
                "inventory-only review remains available."
            )

signals = list(st.session_state.rr_signals or [])

if st.session_state.rr_last_refresh_status == "failed":
    st.error(
        "Live signal unavailable: "
        f"{st.session_state.rr_last_refresh_error}. "
        "Inventory-only review remains available."
    )

    if signals:
        st.caption(
            f"Showing {len(signals)} previous result(s) as cached "
            "session data. These results were not refreshed successfully."
        )

elif st.session_state.rr_last_refresh_status == "success":
    if signals:
        st.success(
            "Last manual TinyFish refresh completed at "
            f"{st.session_state.rr_last_refresh_at} UTC. "
            "Review each source below."
        )
    else:
        st.warning(
            "Live signal unavailable: Search returned no usable source "
            "records. Inventory-only analysis remains available."
        )

elif signals:
    st.info(
        f"Showing {len(signals)} cached result(s). "
        "No API request was made on this rerun."
    )

elif not settings.tinyfish_api_key:
    st.warning(
        "Live signal unavailable until TINYFISH_API_KEY is configured. "
        "Forecast and inventory-only review are available."
    )

else:
    st.caption(
        "TinyFish is configured, but no live request has been made yet."
    )


# Load and validate inventory independently from TinyFish.
inventory, validation_messages = load_inventory()

if validation_messages:
    for message in validation_messages:
        st.warning(message)

if inventory.empty:
    st.error(
        "Inventory data could not be loaded. "
        "Check data/synthetic_demand_inventory.csv."
    )
    st.stop()

if validation_messages and any(
    "Missing required columns" in message
    or "no rows" in message
    or "Could not read" in message
    for message in validation_messages
):
    st.stop()

risk_frame = make_forecast_and_risk(
    inventory,
    horizon_days,
    signals,
)

if risk_frame.empty:
    st.error("No forecast or risk results could be calculated.")
    st.stop()


# 1. Overview and risk distribution
st.subheader("Overview")

metric_cols = st.columns(4)

metric_cols[0].metric(
    "Inventory categories",
    int(inventory["category"].nunique()),
)

metric_cols[1].metric(
    "Historical demand rows",
    int(len(inventory)),
)

metric_cols[2].metric(
    "High-risk categories",
    int((risk_frame["Risk level"] == "High").sum()),
)

metric_cols[3].metric(
    "Forecast horizon",
    f"{horizon_days} days",
)

left, right = st.columns(2)

with left:
    st.markdown("**Heuristic risk scores by category**")
    st.bar_chart(
        risk_frame.set_index("Category")[["Risk score (heuristic)"]]
    )

with right:
    st.markdown("**Average demand per day**")
    st.bar_chart(
        risk_frame.set_index("Category")[["Average demand/day"]]
    )

st.caption(
    "These scores are review priorities, not probabilities or automatic "
    "decisions."
)


# 2. Forecast and stock coverage
st.subheader("Demand forecast and stock coverage")

forecast_columns = [
    "Category",
    "Average demand/day",
    "Forecast horizon (days)",
    "Forecast demand",
    "Available stock",
    "Incoming quantity (undated)",
    "Stock coverage (days)",
    "Supplier lead time (days)",
    "Demand during lead time",
]

st.dataframe(
    risk_frame[forecast_columns],
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Forecast baseline: the mean of the latest seven synthetic daily-demand "
    "rows, held constant across the selected horizon. Stock coverage uses "
    "available stock only. Incoming quantity is shown separately because "
    "this dataset has no arrival date."
)


# 3. Public signals and evidence
st.subheader("Public signals and traceable evidence")

if not signals:
    st.write(
        "No public evidence is available in this session. "
        "Inventory-only forecasting and risk review remain usable."
    )

else:
    for index, signal in enumerate(signals, start=1):
        source_title = str(
            signal.get("source_title") or f"Public source {index}"
        )

        with st.expander(
            source_title,
            expanded=(index == 1),
        ):
            cols = st.columns(3)

            cols[0].write(
                "**Review status**\n\n"
                f"{signal.get('review_status', 'needs_review')}"
            )

            cols[1].write(
                "**Fetch status**\n\n"
                f"{signal.get('fetch_status', 'unknown')}"
            )

            cols[2].write(
                "**Retrieved at (UTC)**\n\n"
                f"{signal.get('retrieved_at') or 'Unavailable'}"
            )

            source_url = signal.get("source_url")

            if source_url:
                st.markdown(
                    f"**Source URL:** [{source_url}]({source_url})"
                )

            st.write("**Publication date supplied by Search**")
            st.write(
                signal.get("published_at")
                or "Not supplied. Retrieval time is not a substitute "
                   "for publication time."
            )

            st.write("**Evidence excerpt**")
            st.text(
                signal.get("evidence_excerpt")
                or "No usable fetched excerpt returned."
            )

            st.caption(
                signal.get("status_note")
                or "Evidence requires human review."
            )

            if signal.get("fetch_status") != "fetched":
                st.warning(
                    "This source did not yield usable fetched page text. "
                    "Do not treat the Search snippet as fetched evidence."
                )


# 4. Explainable risk panel
st.subheader("Risk explanations")

for _, row in risk_frame.iterrows():
    category = row["Category"]
    score = row["Risk score (heuristic)"]
    level = row["Risk level"]

    with st.expander(
        f"{category} — {level} ({score}/100)",
        expanded=True,
    ):
        component_rows = [
            {"Component": name, "Points": points}
            for name, points in row["components"].items()
        ]

        st.dataframe(
            pd.DataFrame(component_rows),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("**Why this priority was assigned**")

        for reason in row["reasons"]:
            st.write(f"- {reason}")

        checks = row["signal_checks"]

        if checks:
            st.markdown(
                "**Public-signal eligibility checks for this category**"
            )

            for check in checks:
                label = check["source_title"]
                points_label = (
                    "Eligible (+10 points)"
                    if check["eligible"]
                    else "0 points"
                )

                if check["source_url"]:
                    st.markdown(
                        f"- [{label}]({check['source_url']}) — "
                        f"{points_label}: {check['reason']}"
                    )
                else:
                    st.write(
                        f"- {label} — {points_label}: {check['reason']}"
                    )

        else:
            st.write(
                "No retrieved public sources were evaluated. "
                "This is an inventory-only score."
            )


# 5. Human-review checklist
st.subheader("Human-review checklist")

st.write(
    "Review the inventory inputs and public evidence before making a "
    "decision. This app does not place orders or execute operational actions."
)

for category in risk_frame["Category"].tolist():
    with st.expander(f"Review checklist — {category}"):
        st.checkbox(
            "Confirm the synthetic inventory and demand inputs.",
            key=f"rr_inputs_{category}",
        )

        st.checkbox(
            "Open the source URL and verify the excerpt, publication date, "
            "and context.",
            key=f"rr_source_{category}",
        )

        st.checkbox(
            "Confirm that the public signal genuinely matches this category.",
            key=f"rr_relevance_{category}",
        )

        st.checkbox(
            "Record a human decision; do not treat the heuristic score "
            "as an instruction.",
            key=f"rr_decision_{category}",
        )


# 6. Transparency and scoring notes
with st.expander("Data, scoring, and integration notes"):
    st.markdown(
        "- Inventory history in this demo is synthetic and non-operational.\n"
        "- Forecast method: seven-row moving average, held constant over "
        "the selected horizon.\n"
        "- Risk score is a heuristic, not a calibrated probability.\n"
        "- A public signal adds points only if its text matches a category, "
        "Search supplies a valid publication date no more than seven days "
        "old, and Fetch returns usable page text.\n"
        "- If Search does not provide publication metadata, the signal "
        "can be displayed but adds zero points.\n"
        "- Cached responses are identified as cached, not live.\n"
        "- TinyFish is called only after a manual refresh-button click.\n"
        "- Reconcile these baseline helpers with your teammates' final "
        "data, forecasting, and risk modules before final submission."
    )