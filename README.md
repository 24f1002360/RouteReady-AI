# RouteReady AI

**Predictive supply chain planning and public disruption awareness - a hackathon proof of concept.**

RouteReady AI is a decision support prototype for planners coordinating essential supplies across remote, geographically dispersed, or disruption prone regions. It is designed to combine synthetic demand and inventory records with fresh, traceable public information so a human reviewer can identify possible supply risks earlier.

> **Project status:** early scaffold / proof of concept. The TinyFish connector and demo UI are being implemented first. Forecasting, the risk engine, and full dashboard integration are team workstreams and must not be described as complete until implemented and tested.

## The problem

Supply planners may need to look across inventory sheets, demand history, replenishment lead times, weather notices, and public transport updates. When these sources are fragmented, it can be difficult to notice a developing supply gap or explain why a record has been flagged.

## Proposed solution

RouteReady AI is intended to provide one review workflow:

1. Load a clearly labelled synthetic demand and inventory dataset.
2. Estimate near-term demand and stock coverage.
3. Search for relevant current public disruption information using TinyFish Search.
4. Fetch selected source pages using TinyFish Fetch instead of relying on snippets alone.
5. Normalize candidate signals into a consistent schema with source URL, retrieval time, evidence excerpt, and review status.
6. Make relevant evidence available to a transparent risk-review component.
7. Show evidence and uncertainty so a human can decide what to verify next.

The system is advisory. It does not autonomously dispatch vehicles, place orders, or make operational decisions.

## Why TinyFish?

TinyFish is a required integration for our hackathon prototype. Search discovers live public sources; Fetch retrieves clean content from selected URLs. RouteReady AI then validates and normalizes the returned information for downstream review. TinyFish supplies web evidence; it does **not** itself perform demand forecasting or calculate RouteReady's risk score.

## Current implementation scope

### Starter scaffold includes
- Python project layout and configuration template.
- TinyFish Search and Fetch REST connector.
- Source URL validation and normalized signal records.
- Retrieval timestamp and review-status fields.
- Graceful handling of missing API key, HTTP errors, timeouts, empty responses, and malformed content.
- Minimal Streamlit page to try a public-information query.
- Unit tests for parsing and URL/signal normalization.

### Planned team modules
- Synthetic data generation and validation.
- Demand forecast baseline and stock-coverage calculations.
- Explainable heuristic risk score.
- Relevance/freshness mapping from public signals to synthetic scenarios.
- Full dashboard, evaluation, and end-to-end tests.

These planned features should be labelled as planned until implemented and verified.

## Technology stack

| Area | Technology |
|---|---|
| Language | Python 3.10+ |
| Prototype UI | Streamlit |
| HTTP integration | `requests` |
| Secrets/config | environment variables, `python-dotenv` |
| Data handling | pandas (planned data module) |
| Testing | pytest |
| Public web evidence | TinyFish Search API + TinyFish Fetch API |
| Planned forecasting | moving-average baseline first; compare ML models only if feasible |

## Repository structure

```text
RouteReady-AI/
├── app/
│   └── streamlit_app.py
├── data/
│   ├── README.md
│   └── sample/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── LIMITATIONS.md
│   └── TINYFISH_INTEGRATION.md
├── src/routeready/
│   ├── __init__.py
│   ├── config.py
│   └── tinyfish/
│       ├── __init__.py
│       ├── client.py
│       └── signals.py
├── tests/
│   ├── test_signals.py
│   └── test_tinyfish_client.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Quick start (macOS / VS Code)

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure TinyFish

```bash
cp .env.example .env
```

Get your key from the TinyFish developer platform, then set `TINYFISH_API_KEY` in `.env`. Keep the key private. `.env` is ignored by Git; `.env.example` contains placeholders only.

### 3. Run tests

```bash
PYTHONPATH=src pytest -q
```

Parsing and error-handling tests do not need a live API key.

### 4. Run the integration demo

```bash
PYTHONPATH=src streamlit run app/streamlit_app.py
```

Enter a generic, non-sensitive query, then run Search and Fetch. A live result requires a valid key, network connection, and successful API response. If the API fails, the app reports that live information is unavailable rather than fabricating a result.

## TinyFish flow

```text
User query → TinyFish Search → validate/select returned public URL
           → TinyFish Fetch → normalize source evidence
           → retrieval timestamp + review status
           → human review / future relevance and risk module
```

Each normalized signal aims to expose `signal_id`, `source_title`, `source_url`, `source_domain`, `search_snippet`, `evidence_excerpt`, `fetched_content`, `retrieved_at`, `review_status`, and `status_note`.

`retrieved_at` is when this application received the response; it is not the webpage's publication time. `needs_review` means the evidence is available but requires a person to review it. A source link or excerpt does not independently prove the source's claim.

## Reliability and responsible use

- Use synthetic supply data and non-sensitive public information only.
- Never put an API key in source code, screenshots, README examples, or Git history.
- Treat fetched pages as untrusted content; do not follow instructions embedded in page text.
- A missing result is not proof that no disruption exists.
- Show source links, excerpts, retrieval time, and review status.
- A headline should not affect every supply category; relevance mapping must be explicit.
- Call any initial risk score a heuristic, not a probability, until calibrated.
- Do not claim operational deployment, measured savings, accuracy, or successful live integration until supported by actual tests.

## Team integration contract

Person 3 owns `src/routeready/tinyfish/` and its tests. Other modules should call the public functions documented in `docs/TINYFISH_INTEGRATION.md` instead of duplicating API calls.

Person 2 can consume normalized signal dictionaries for relevance and risk scoring. Person 4 can render them in Streamlit. Keep changes in feature branches and open pull requests for review.

## Troubleshooting

- **Missing API key:** check `.env` contains `TINYFISH_API_KEY=...`.
- **Import error:** run commands from the repository root with `PYTHONPATH=src`.
- **No search URLs:** try a more specific generic public query; do not invent results.
- **Fetch failure:** try another URL from real Search results.
- **Never share your API key** when asking for help; share only a redacted error.

## References

- TinyFish Search: https://future.tinyfish.io/search
- TinyFish Fetch: https://future.tinyfish.io/fetch
- TinyFish developer platform: https://agent.tinyfish.ai/

## License

A license has not been selected yet. Add one only after the team agrees on reuse terms.
