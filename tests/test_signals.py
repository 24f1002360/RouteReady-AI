from routeready.tinyfish.signals import extract_text, is_safe_public_url, normalize_signal


def test_public_url_validation():
    assert is_safe_public_url("https://example.com/path")
    assert not is_safe_public_url("file:///etc/passwd")
    assert not is_safe_public_url("http://localhost:8501")
    assert not is_safe_public_url("http://192.168.1.1")


def test_extract_text_from_common_payloads():
    assert extract_text({"markdown": "# Notice\nRoad closed"}) == "# Notice\nRoad closed"
    assert "Forecast" in extract_text({"data": {"content": "Forecast update"}})
    assert extract_text({"status": "ok"}) == ""


def test_normalize_signal_is_traceable_and_needs_review():
    signal = normalize_signal(
        {"title": "Public notice", "url": "https://example.com/notice", "snippet": "A public update"},
        {"markdown": "A public transport notice has been published."},
    )
    assert signal["source_url"] == "https://example.com/notice"
    assert signal["source_domain"] == "example.com"
    assert signal["retrieved_at"]
    assert signal["review_status"] == "needs_review"
    assert "transport notice" in signal["evidence_excerpt"]
