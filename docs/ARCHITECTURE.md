# RouteReady AI — Architecture

```text
Synthetic demand / inventory CSV
             |
             v
   Validation + forecast baseline
             |
             +------------------------------+
                                            |
User query -> TinyFish Search -> URL checks |
                         |                  |
                         v                  |
                   TinyFish Fetch           |
                         |                  |
                         v                  |
            Normalize source evidence       |
            (URL, excerpt, retrieval time)  |
                         |                  |
                         +--------+---------+
                                  v
                     Relevance + freshness rules
                                  |
                                  v
                     Explainable risk-review queue
                                  |
                                  v
                     Streamlit UI / human review
```

## Current versus planned

The current scaffold provides the TinyFish connector, signal normalization, a small demo page, and basic unit tests. Forecasting, the full risk engine, and integrated dashboard are planned modules; do not describe them as implemented until merged and tested.

## Integration boundaries

- TinyFish client returns normalized signal dictionaries.
- Forecasting module should accept validated synthetic data and return forecast/coverage fields.
- Risk module should combine outputs using documented, explicit rules.
- UI should render source evidence and status, not silently convert a headline into a confirmed fact.
