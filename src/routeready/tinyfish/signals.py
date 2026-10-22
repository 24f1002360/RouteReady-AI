"""Normalize TinyFish responses into RouteReady signal records."""
from datetime import datetime, timezone
from hashlib import sha256
from urllib.parse import urlparse
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def is_safe_public_url(url: str) -> bool:
    """Basic guard: allow public HTTP(S), reject common local/private hosts."""
    if not isinstance(url, str) or not url.strip():
        return False
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return False
    parts = host.split(".")
    if len(parts) == 4 and all(part.isdigit() for part in parts):
        octets = [int(part) for part in parts]
        if any(o > 255 for o in octets):
            return False
        a, b, _, _ = octets
        if a in {10, 127} or (a == 169 and b == 254) or (a == 192 and b == 168):
            return False
        if a == 172 and 16 <= b <= 31:
            return False
    return True


def _first_string(mapping: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def extract_text(payload: Any) -> str:
    """Extract readable text from common Fetch response shapes."""
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, list):
        return "\n".join(x for x in (extract_text(v) for v in payload) if x)
    if not isinstance(payload, dict):
        return ""
    for key in ("markdown", "content", "text", "html", "body", "data", "result"):
        if key in payload:
            result = extract_text(payload[key])
            if result:
                return result
    chunks = []
    for value in payload.values():
        if isinstance(value, (dict, list)):
            result = extract_text(value)
            if result:
                chunks.append(result)
    return "\n".join(chunks).strip()


def normalize_signal(search_result: dict, fetch_payload: Any = None) -> dict:
    """Return a stable, downstream-friendly signal record."""
    title = _first_string(search_result, ("title", "name", "page_title")) or "Untitled public source"
    url = _first_string(search_result, ("url", "link", "source_url"))
    snippet = _first_string(search_result, ("snippet", "description", "summary"))
    domain = urlparse(url).hostname if url and is_safe_public_url(url) else ""
    fetched_text = extract_text(fetch_payload) if fetch_payload is not None else ""
    content = fetched_text[:12000]
    evidence = content or snippet
    excerpt = " ".join(evidence.split())[:500]
    signal_id = sha256(f"{url}|{title}".encode("utf-8", errors="ignore")).hexdigest()[:16]
    if not url or not is_safe_public_url(url):
        status, note = "unusable", "Search result did not contain a valid public HTTP(S) source URL."
    elif not content:
        status, note = "needs_review", "A source URL was found, but usable fetched page text was unavailable."
    else:
        status, note = "needs_review", "Fetched content is available; a human should confirm relevance and factual context."
    return {
        "signal_id": signal_id,
        "source_title": title,
        "source_url": url,
        "source_domain": domain or "",
        "search_snippet": snippet,
        "evidence_excerpt": excerpt,
        "fetched_content": content,
        "retrieved_at": utc_now_iso(),
        "review_status": status,
        "status_note": note,
    }
