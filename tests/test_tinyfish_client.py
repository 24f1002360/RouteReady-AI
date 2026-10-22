import pytest
from routeready.config import Settings
from routeready.tinyfish.client import TinyFishClient, TinyFishError


def settings(key="test-key"):
    return Settings(
        tinyfish_api_key=key,
        tinyfish_search_url="https://api.search.tinyfish.ai",
        tinyfish_fetch_url="https://api.fetch.tinyfish.ai",
        timeout_seconds=2,
        max_results=3,
    )


def test_missing_key_fails_clearly():
    client = TinyFishClient(settings(key=""))
    with pytest.raises(TinyFishError, match="TINYFISH_API_KEY"):
        client.search("public weather notice")


def test_blank_query_fails_before_request():
    client = TinyFishClient(settings())
    with pytest.raises(TinyFishError, match="search query"):
        client.search("  ")


def test_fetch_rejects_local_url_before_request():
    client = TinyFishClient(settings())
    with pytest.raises(TinyFishError, match="public HTTP"):
        client.fetch("http://127.0.0.1:8000")
