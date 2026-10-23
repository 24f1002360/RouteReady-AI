# RouteReady AI 🧭

**Evidence-aware supply planning with demand baselines, stock-coverage estimates, and live public disruption signals powered by TinyFish.**

RouteReady AI is a Streamlit decision-support prototype for exploring how planners could spot potential supply risks earlier. It combines clearly labelled synthetic inventory and demand data with public information retrieved from the live web through TinyFish Search and Fetch. The dashboard presents the evidence, explains its heuristic risk priorities, and leaves decisions to a human reviewer.

> **Hackathon:** Kritical Hacks 2026 · **Track:** AI/ML - Open Innovation · **Required integration:** TinyFish

## Project links

- 🎬 **Demo video:** [Add demo video link](https://drive.google.com/file/d/1ORR57vcXVH-zmAqpGrm81MiovcNPe70r/view?usp=sharing)
- 📊 **Presentation / PPT / PDF:** [Add presentation link](https://drive.google.com/file/d/1e4QF5VCPIax_Nmfd6mdPgj2DrR3yhBoR/view?usp=drive_link)
- 🌐 **Linkdin Post:** [Add deployed app link](https://www.linkedin.com/feed/update/urn:li:ugcPost:7519095414705348608?openCollaboratorList=false)


Replace the placeholders above with the final public links before submission. If a link is not available yet, leave it clearly marked as pending rather than linking to a non-existent resource.

## The problem

Supply planning often requires people to compare inventory, demand, replenishment lead times, and public updates such as weather advisories or transport disruptions. These signals can be scattered across different sources, making it harder to notice a potential shortage and explain why it deserves attention.

## Our solution

RouteReady AI brings a small set of planning indicators and source evidence into one review workflow. It currently demonstrates:

- **Demand baseline:** calculates average daily demand from recent synthetic history and projects it over a user-selected horizon.
- **Stock coverage:** estimates how many days the available stock could cover at the recent average demand rate.
- **Heuristic risk prioritization:** assigns a transparent score and Low / Moderate / High level using stock coverage, supplier lead time, demand variability, replenishment uncertainty, and qualifying public signals.
- **Live public-web evidence:** uses TinyFish Search to discover public pages and TinyFish Fetch to retrieve page content.
- **Category relevance and freshness checks:** checks whether fetched content appears relevant to a demo supply category and whether publication-date metadata indicates a sufficiently recent signal.
- **Evidence traceability:** displays source URLs, excerpts, retrieval timestamps, and review/fetch status so users can inspect the underlying information.
- **Human-review checklist:** prompts reviewers to validate inventory inputs, source context, category relevance, and the final decision.
- **Graceful fallback:** inventory-only forecasting and risk review remain available when live TinyFish information cannot be retrieved.

All inventory examples are synthetic. This is a prototype for decision support, not a production logistics system.

## TinyFish integration - mandatory for Kritical Hacks 2026

TinyFish is used as a functional part of the application, not just mentioned in the documentation.

### How it works

1. A user manually triggers a public-information refresh in the main dashboard and enters or selects a query.
2. **TinyFish Search API** finds candidate public web pages.
3. RouteReady AI validates candidate URLs before attempting to fetch them.
4. **TinyFish Fetch API** retrieves page content from selected public URLs.
5. The application normalizes results into signal records, including source title, URL/domain, evidence excerpt, fetched content, retrieval time, fetch status, and review status.
6. Category and freshness checks determine whether a signal qualifies to contribute a limited bonus to the heuristic score. A Search snippet alone is not treated as fetched evidence.
7. The dashboard shows the evidence and the reason a signal did or did not qualify; a human must review it before acting.

TinyFish supplies live web discovery and retrieval. It does not perform RouteReady AI's demand calculation or independently determine the supply-risk score.

**Important:** A valid `TINYFISH_API_KEY` and network access are needed for live requests. If the key is missing or the API request fails, the application should report that live evidence is unavailable rather than fabricate results. The separate integration-demo page is also available for trying Search + Fetch directly.

## How the risk score works

The dashboard calculates an **explainable heuristic score from 0 to 100**. The current score uses these components:

| Component | Maximum points | Purpose |
|---|---:|---|
| Stock coverage pressure | 40 | Compares estimated stock coverage with supplier lead time and nearby coverage thresholds |
| Supplier lead-time pressure | 25 | Adds pressure for longer replenishment lead times |
| Recent demand variability | 15 | Accounts for variation in the recent demand window |
| Replenishment uncertainty | 10 | Treats incoming quantity cautiously because the sample data does not confirm an arrival date |
| Fresh, relevant fetched public signal | 10 | Adds a capped bonus only when a signal passes the current relevance, freshness, and fetched-content checks |

The current display maps scores to **Low** (below 40), **Moderate** (40–69), and **High** (70 or above). The demand baseline uses the mean of the latest seven daily-demand rows and holds that average constant over the selected forecast horizon. Stock coverage uses available stock; undated incoming stock is shown separately and is not counted as confirmed near-term supply.

These rules are transparent prototype heuristics, **not calibrated probabilities or validated operational predictions**. Public information can be incomplete, outdated, incorrectly interpreted, or unrelated to a particular supply category. A missing signal does not prove that no disruption exists.

## Technology stack

- **Language:** Python
- **Dashboard:** Streamlit
- **Data processing:** pandas
- **HTTP/API integration:** requests
- **Configuration:** python-dotenv and environment variables
- **Live-web retrieval:** TinyFish Search API and TinyFish Fetch API
- **Testing:** pytest

## Repository structure

```text
RouteReady-AI-main/
├── app.py                              # Main integrated dashboard
├── app/
│   └── streamlit_app.py                # TinyFish Search + Fetch demo
├── data/
│   ├── README.md                       # Dataset notes and schema
│   ├── sample/
│   │   └── inventory.csv               # Synthetic sample dataset
│   └── synthetic_demand_inventory.csv  # Dataset used by the main dashboard
├── docs/
│   ├── ARCHITECTURE.md                 # System architecture notes
│   ├── LIMITATIONS.md                  # Known limitations
│   └── TINYFISH_INTEGRATION.md          # TinyFish integration contract
├── src/routeready/
│   ├── config.py                       # Environment-backed settings
│   ├── data/                           # Data generation, schema, validation/loading
│   └── tinyfish/                       # TinyFish client and signal normalization
├── tests/                              # Unit tests
├── .env.example                        # Environment variable template
├── requirements.txt
└── README.md
```

## Run locally

### 1. Requirements

- Python 3.10 or newer
- `pip`
- A TinyFish API key for live public-web retrieval (the dashboard's inventory-only features can be explored without live results)

### 2. Clone the repository and enter its folder

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd RouteReady-AI-main
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your repository URL. If you already downloaded the project ZIP, extract it and open a terminal in the extracted project directory.

### 3. Create and activate a virtual environment

**Windows PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file from the template:

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux**

```bash
cp .env.example .env
```

Open `.env` and set your own private TinyFish API key:

```dotenv
TINYFISH_API_KEY=your_private_tinyfish_api_key
TINYFISH_SEARCH_URL=https://api.search.tinyfish.ai
TINYFISH_FETCH_URL=https://api.fetch.tinyfish.ai
TINYFISH_TIMEOUT_SECONDS=30
TINYFISH_MAX_RESULTS=5
```

Get access through the [TinyFish developer platform](https://agent.tinyfish.ai/). Keep `.env` private and never commit real credentials. The `.env.example` file in the repository should contain placeholders only.

### 5. Start the main dashboard

From the repository root:

```bash
streamlit run app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`) to open in your browser. The main dashboard includes the synthetic demand baseline, stock coverage, category-level heuristic risk review, public-signal evidence, and a human-review checklist.

### 6. Run the standalone TinyFish integration demo

To test the Search + Fetch flow separately:

```bash
PYTHONPATH=src streamlit run app/streamlit_app.py
```

On Windows PowerShell, if `PYTHONPATH=src` does not work in your shell, set the variable first:

```powershell
$env:PYTHONPATH = "src"
streamlit run app/streamlit_app.py
```

Use a generic public-information query. Avoid entering private, sensitive, or operationally confidential route details.

### 7. Run the tests

```bash
PYTHONPATH=src pytest -q
```

Windows PowerShell alternative:

```powershell
$env:PYTHONPATH = "src"
pytest -q
```

The repository test suite was run against the uploaded project snapshot: **22 tests passed**. Tests do not establish the availability of the live TinyFish service or validate real-world forecast accuracy.

## Demo walkthrough

For a hackathon demo, this order shows the core workflow clearly:

1. Open the main dashboard and explain the supply-planning problem.
2. Show the synthetic data disclaimer and the demand/stock-coverage overview.
3. Expand a category's risk explanation and walk through the score components.
4. Trigger a TinyFish refresh to demonstrate live Search and Fetch.
5. Open a source link and show the fetched excerpt, retrieval timestamp, and review status.
6. Explain why a signal qualifies or does not qualify for a category; emphasize that a search snippet alone is insufficient.
7. Finish with the human-review checklist and explain why RouteReady AI supports decisions instead of taking autonomous operational action.

For evaluation, be prepared to demonstrate the live integration using your own valid key. Do not show the key on screen or place it in slides, recordings, screenshots, or Git history.

## Responsible use and limitations

- The supplied inventory and demand records are synthetic demonstrations, not real operational data.
- Risk scores are heuristic priorities, not probabilities, and have not been validated against real supply-chain outcomes.
- Forecasts are simple moving-average baselines, not advanced machine-learning forecasts.
- Incoming quantities have no confirmed arrival dates and are not treated as guaranteed available stock.
- Public sources must be checked for context, publication date, credibility, and relevance.
- A source excerpt is evidence to review, not automatic confirmation that a claim is true.
- Live requests depend on API credentials, network access, provider availability, and the returned source content.
- RouteReady AI does not place orders, dispatch vehicles, or autonomously make operational decisions.

See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), and [`docs/TINYFISH_INTEGRATION.md`](docs/TINYFISH_INTEGRATION.md) for more detail.

## Kritical Hacks 2026 alignment

- **Open Innovation / AI/ML Track:** applies data processing, forecasting baselines, explainable risk heuristics, and live public-web evidence to a practical planning problem.
- **Mandatory TinyFish integration:** implemented through functional Search and Fetch API calls, source normalization, and evidence shown in the dashboard.
- **Pitch requirement:** explain where TinyFish is called, what data it returns, how fetched content is checked, and how the application behaves when live retrieval fails. Demonstrate the flow during evaluation rather than relying on this README alone.
- **Human oversight:** the system exposes evidence and uncertainty and leaves final decisions to a reviewer.

The event organizers' final rules and submission instructions take precedence over this summary.

## References

- [TinyFish developer platform](https://agent.tinyfish.ai/)
- [TinyFish Search API](https://future.tinyfish.io/search)
- [TinyFish Fetch API](https://future.tinyfish.io/fetch)
- [Kritical Hacks 2026 rules and regulations](https://docs.google.com/document/d/1xUDI09_dWUyyTtNW_gKzmseAhTUgb1OIv4HhPp0Wesg/edit?usp=sharing)

## License

No license has been specified yet. Add a license only after the project team agrees on the reuse terms.
