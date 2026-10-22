"""Environment-backed configuration."""
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    tinyfish_api_key: str
    tinyfish_search_url: str
    tinyfish_fetch_url: str
    timeout_seconds: float
    max_results: int

    @classmethod
    def from_env(cls) -> "Settings":
        try:
            timeout = float(os.getenv("TINYFISH_TIMEOUT_SECONDS", "30"))
            max_results = int(os.getenv("TINYFISH_MAX_RESULTS", "5"))
        except ValueError as exc:
            raise ValueError("TinyFish timeout and max-results settings must be numeric.") from exc
        return cls(
            tinyfish_api_key=os.getenv("TINYFISH_API_KEY", "").strip(),
            tinyfish_search_url=os.getenv("TINYFISH_SEARCH_URL", "https://api.search.tinyfish.ai").strip(),
            tinyfish_fetch_url=os.getenv("TINYFISH_FETCH_URL", "https://api.fetch.tinyfish.ai").strip(),
            timeout_seconds=max(1.0, timeout),
            max_results=max(1, min(max_results, 10)),
        )
