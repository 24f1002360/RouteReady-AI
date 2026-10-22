# Person 3 — TinyFish Integration Contract

## Public interface

```python
from routeready.tinyfish import TinyFishClient, TinyFishError

client = TinyFishClient()
search_results = client.search("generic public transport disruption notice")
signals = client.search_and_fetch("generic public weather advisory")
```

`search()` returns raw TinyFish Search result dictionaries with usable public URLs. `fetch(url)` returns the parsed JSON payload from TinyFish Fetch. `search_and_fetch(query)` runs both steps and returns normalized signal dictionaries.

## Signal schema

- `signal_id`
- `source_title`
- `source_url`
- `source_domain`
- `search_snippet`
- `evidence_excerpt`
- `fetched_content`
- `retrieved_at` (UTC timestamp recorded by this application)
- `review_status` (`needs_review` or `unusable` in this initial version)
- `status_note`

Downstream code should use this schema rather than re-parsing provider responses.

## API calls

- Search: `GET https://api.search.tinyfish.ai?query=...`
- Fetch: `POST https://api.fetch.tinyfish.ai` with JSON `{"urls": ["https://..."]}`
- Both use `X-API-Key`.

These details follow TinyFish's published Search/Fetch getting-started material. Re-check official docs if the provider changes its API.

## Failure behavior

- Missing key, timeout, HTTP errors, and invalid JSON raise `TinyFishError` at the client boundary.
- If Search returns no usable URLs, the caller receives an empty list.
- If Fetch fails for one result, `search_and_fetch` retains the Search source with `needs_review` and a clear failure note.
- The UI must show live information unavailable when calls fail. Do not replace failed live results with fabricated data.
- URL validation rejects common local/private addresses; it is a safety guard, not a complete SSRF defense.

## Manual smoke test

1. Set `TINYFISH_API_KEY` in `.env`.
2. Run `PYTHONPATH=src streamlit run app/streamlit_app.py`.
3. Enter a generic public query and click **Search and fetch public sources**.
4. Confirm the UI shows a source URL, retrieval timestamp, excerpt, and `needs_review`.
5. Test with the key removed; the UI should show a clear unavailable message.
6. Save a redacted screenshot for team review. Never include the key.
