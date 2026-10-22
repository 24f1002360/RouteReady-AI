"""Minimal TinyFish integration demo for RouteReady AI."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st
from routeready.config import Settings
from routeready.tinyfish import TinyFishClient, TinyFishError

st.set_page_config(page_title="RouteReady AI | Public Signals", page_icon="🧭", layout="wide")
st.title("RouteReady AI")
st.caption("TinyFish Search → Fetch integration preview | Synthetic planning context only")
st.info("This is an integration demo, not the finished forecasting dashboard. Live public-web signals are evidence candidates and require human review.")

settings = Settings.from_env()
if not settings.tinyfish_api_key:
    st.warning("TinyFish API key is not configured. Copy `.env.example` to `.env` and add your key.")

query = st.text_input(
    "Public-information search query",
    value="public weather advisory or transport disruption notice for disaster relief logistics",
    help="Use generic public queries. Do not enter sensitive routes, operational locations, or private data.",
)

if st.button("Search and fetch public sources", type="primary"):
    if not settings.tinyfish_api_key:
        st.error("Live signal unavailable: TINYFISH_API_KEY is missing. No fake results will be shown.")
    elif not query.strip():
        st.warning("Enter a query first.")
    else:
        with st.spinner("Searching TinyFish and fetching returned public pages..."):
            try:
                signals = TinyFishClient(settings).search_and_fetch(query)
                if not signals:
                    st.warning("Live signal unavailable: Search returned no usable public URLs.")
                else:
                    st.success(f"Received {len(signals)} source record(s). Review each before use.")
                    for signal in signals:
                        with st.expander(signal["source_title"], expanded=True):
                            st.write(f"**Status:** {signal['review_status']}")
                            st.write(f"**Retrieved at (UTC):** {signal['retrieved_at']}")
                            st.write(f"**Domain:** {signal['source_domain'] or 'Unavailable'}")
                            if signal["source_url"]:
                                st.markdown(f"[Open original source]({signal['source_url']})")
                            st.write("**Evidence excerpt**")
                            st.write(signal["evidence_excerpt"] or "No usable excerpt returned.")
                            st.caption(signal["status_note"])
            except TinyFishError as exc:
                st.error(f"Live signal unavailable: {exc}")
            except Exception as exc:
                st.error(f"Live signal unavailable due to an unexpected error ({type(exc).__name__}).")

st.divider()
st.subheader("How this connects to the full project")
st.markdown(
    "- **Person 2:** consume normalized signals and implement explicit relevance/freshness rules.\n"
    "- **Person 4:** render reviewed signal records in the main dashboard.\n"
    "- **Person 1:** provide validated synthetic inventory/demand data.\n\n"
    "A public headline should not automatically raise every category's risk. The risk engine must decide relevance and explain its reasoning."
)
