"""Defensive TinyFish Search + Fetch REST client."""
from typing import Any
import requests
from routeready.config import Settings
from .signals import is_safe_public_url, normalize_signal


class TinyFishError(RuntimeError):
    """A TinyFish request failed or returned unusable data."""


class TinyFishClient:
    def __init__(self, settings: Settings | None = None, session: Any = None):
        self.settings = settings or Settings.from_env()
        self.session = session or requests.Session()

    def _headers(self) -> dict[str, str]:
        if not self.settings.tinyfish_api_key:
            raise TinyFishError("TINYFISH_API_KEY is missing. Copy .env.example to .env and add your key.")
        return {"X-API-Key": self.settings.tinyfish_api_key}

    def search(self, query: str) -> list[dict]:
        query = (query or "").strip()
        if not query:
            raise TinyFishError("Enter a search query.")
        try:
            response = self.session.get(
                self.settings.tinyfish_search_url,
                params={"query": query},
                headers=self._headers(),
                timeout=self.settings.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except TinyFishError:
            raise
        except requests.Timeout as exc:
            raise TinyFishError("TinyFish Search timed out. Try again shortly.") from exc
        except requests.RequestException as exc:
            raise TinyFishError(f"TinyFish Search request failed: {exc}") from exc
        except ValueError as exc:
            raise TinyFishError("TinyFish Search returned a non-JSON response.") from exc

        if not isinstance(payload, dict):
            raise TinyFishError("TinyFish Search returned an unexpected response format.")
        results = payload.get("results", [])
        if not isinstance(results, list):
            raise TinyFishError("TinyFish Search response did not contain a results list.")
        normalized = []
        for result in results:
            if not isinstance(result, dict):
                continue
            url = result.get("url") or result.get("link") or result.get("source_url")
            if isinstance(url, str) and is_safe_public_url(url):
                normalized.append(result)
            if len(normalized) >= self.settings.max_results:
                break
        return normalized

    def fetch(self, url: str) -> Any:
        if not is_safe_public_url(url):
            raise TinyFishError("Fetch URL must be a public HTTP(S) URL.")
        try:
            response = self.session.post(
                self.settings.tinyfish_fetch_url,
                json={"urls": [url]},
                headers={**self._headers(), "Content-Type": "application/json"},
                timeout=self.settings.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except TinyFishError:
            raise
        except requests.Timeout as exc:
            raise TinyFishError("TinyFish Fetch timed out. Try another public source.") from exc
        except requests.RequestException as exc:
            raise TinyFishError(f"TinyFish Fetch request failed: {exc}") from exc
        except ValueError as exc:
            raise TinyFishError("TinyFish Fetch returned a non-JSON response.") from exc

    def search_and_fetch(self, query: str) -> list[dict]:
        signals = []
        for result in self.search(query):
            url = result.get("url") or result.get("link") or result.get("source_url")
            try:
                signal = normalize_signal(result, self.fetch(url))
            except TinyFishError as exc:
                signal = normalize_signal(result, None)
                signal["status_note"] = f"Fetch failed: {exc}"
                signal["review_status"] = "needs_review"
            signals.append(signal)
        return signals
