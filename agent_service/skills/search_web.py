from __future__ import annotations

from typing import Any

import httpx


def search_web(query: str, max_results: int = 5) -> dict[str, Any]:
    params = {
        "q": query,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1,
    }
    try:
        with httpx.Client(timeout=20) as client:
            response = client.get("https://api.duckduckgo.com/", params=params)
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        return {"ok": False, "query": query, "error": str(exc), "results": []}

    results: list[dict[str, str]] = []
    abstract = str(payload.get("AbstractText") or "").strip()
    abstract_url = str(payload.get("AbstractURL") or "").strip()
    if abstract:
        results.append({"title": "Abstract", "snippet": abstract, "url": abstract_url})

    for topic in payload.get("RelatedTopics", []):
        if len(results) >= max_results:
            break
        if isinstance(topic, dict) and "Text" in topic and "FirstURL" in topic:
            results.append(
                {
                    "title": str(topic.get("Text", ""))[:120],
                    "snippet": str(topic.get("Text", "")),
                    "url": str(topic.get("FirstURL", "")),
                }
            )

    return {"ok": True, "query": query, "results": results[:max_results]}

