from __future__ import annotations

import json
import time
from typing import Any

import httpx


def _duckduckgo_api_results(query: str, max_results: int = 5) -> list[dict[str, str]]:
    params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
    try:
        with httpx.Client(timeout=15) as client:
            response = client.get("https://api.duckduckgo.com/", params=params)
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return []

    results: list[dict[str, str]] = []
    abstract = str(payload.get("AbstractText") or "").strip()
    abstract_url = str(payload.get("AbstractURL") or "").strip()
    if abstract:
        results.append({"title": "Abstract", "url": abstract_url, "snippet": abstract})
    for topic in payload.get("RelatedTopics", []):
        if len(results) >= max_results:
            break
        if isinstance(topic, dict) and "Text" in topic and "FirstURL" in topic:
            results.append(
                {
                    "title": str(topic.get("Text", ""))[:120],
                    "url": str(topic.get("FirstURL", "")),
                    "snippet": str(topic.get("Text", "")),
                }
            )
    return results[:max_results]


def browser_use(
    action: str,
    url: str | None = None,
    selector: str | None = None,
    text: str | None = None,
    timeout_ms: int = 15_000,
) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return {"ok": False, "error": "playwright is not installed"}

    if action == "open" and not url:
        return {"ok": False, "error": "url is required for open"}
    if action in {"click", "type", "extract"} and not selector:
        return {"ok": False, "error": "selector is required"}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        if url:
            page.goto(url, timeout=timeout_ms)

        if action == "open":
            result = {"ok": True, "title": page.title(), "url": page.url}
        elif action == "click":
            page.click(selector=selector, timeout=timeout_ms)
            result = {"ok": True, "clicked": selector}
        elif action == "type":
            page.fill(selector=selector, value=text or "", timeout=timeout_ms)
            result = {"ok": True, "typed": selector, "text_len": len(text or "")}
        elif action == "extract":
            content = page.text_content(selector=selector, timeout=timeout_ms) or ""
            result = {"ok": True, "selector": selector, "content": content.strip()}
        else:
            result = {"ok": False, "error": f"unsupported action: {action}"}

        browser.close()
        return result


def browser_google_search(
    query: str,
    url: str = "https://www.google.com",
    timeout_ms: int = 20_000,
    headless: bool = False,
    fallback_engine: str = "duckduckgo",
    fallback_on_verification: bool = True,
    wait_for_user_on_verification: bool = True,
    manual_wait_timeout_sec: int = 300,
    verification_poll_interval_sec: int = 5,
) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return {"ok": False, "error": "playwright is not installed"}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url, timeout=timeout_ms)
        page.fill("textarea[name='q']", query, timeout=timeout_ms)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1800)

        verification_hints = [
            "unusual traffic",
            "verify you are human",
            "detected unusual traffic",
            "sorry",
            "captcha",
            "not a robot",
            "recaptcha",
        ]
        def get_page_snapshot() -> dict[str, Any]:
            title = ""
            body = ""
            current_url = ""
            try:
                title = page.title()
            except Exception:
                pass
            try:
                current_url = page.url
            except Exception:
                pass
            try:
                body = (page.locator("body").inner_text(timeout=timeout_ms) or "")[:12000]
            except Exception:
                body = ""
            return {
                "title": title,
                "url": current_url,
                "body": body,
            }

        def has_verification(snapshot: dict[str, Any]) -> bool:
            title = str(snapshot.get("title", "")).lower()
            body = str(snapshot.get("body", "")).lower()
            current_url = str(snapshot.get("url", "")).lower()
            url_hints = ["/sorry/", "captcha", "recaptcha", "challenge"]
            url_match = any(h in current_url for h in url_hints)
            body_match = any(h in body for h in verification_hints)
            return url_match or body_match or "captcha" in title or "verify" in title

        snapshot = get_page_snapshot()
        verification_detected = has_verification(snapshot)

        if verification_detected and wait_for_user_on_verification and not headless:
            deadline = time.time() + max(30, manual_wait_timeout_sec)
            while time.time() < deadline:
                page.wait_for_timeout(max(1, verification_poll_interval_sec) * 1000)
                snapshot = get_page_snapshot()
                if not has_verification(snapshot):
                    page.wait_for_timeout(1200)
                    result_payload = page.evaluate(
                        """
                        () => {
                          const nodes = Array.from(document.querySelectorAll('div.g'));
                          const top = nodes.slice(0, 5).map((n) => {
                            const a = n.querySelector('a');
                            const h3 = n.querySelector('h3');
                            return {
                              title: h3 ? h3.innerText : '',
                              url: a ? a.href : ''
                            };
                          }).filter((x) => x.title && x.url);
                          return {
                            page_title: document.title,
                            current_url: location.href,
                            top_results: top
                          };
                        }
                        """
                    )
                    browser.close()
                    return {
                        "ok": True,
                        "query": query,
                        "engine": "google",
                        "verification_detected": False,
                        "manual_verification_used": True,
                        "verification_wait_seconds": int(max(0, manual_wait_timeout_sec - (deadline - time.time()))),
                        "results": result_payload,
                        "raw": json.dumps(result_payload),
                    }
            browser.close()
            return {
                "ok": False,
                "query": query,
                "engine": "google",
                "verification_detected": True,
                "state": "manual_verification_timeout",
                "verification_url": snapshot.get("url", ""),
                "error": "Timed out waiting for manual verification to complete.",
            }

        if verification_detected and fallback_on_verification:
            if fallback_engine == "duckduckgo":
                page.goto(f"https://duckduckgo.com/?q={query}", timeout=timeout_ms)
                page.wait_for_timeout(1200)
                result_payload = page.evaluate(
                    """
                    () => {
                      const nodes = Array.from(document.querySelectorAll('article h2 a, .result__a'));
                      const top = nodes.slice(0, 5).map((a) => ({
                        title: a.textContent || '',
                        url: a.href || ''
                      })).filter((x) => x.title && x.url);
                      return {
                        page_title: document.title,
                        current_url: location.href,
                        top_results: top
                      };
                    }
                    """
                )
                if not result_payload.get("top_results"):
                    result_payload["top_results"] = _duckduckgo_api_results(query=query, max_results=5)
                browser.close()
                return {
                    "ok": True,
                    "query": query,
                    "engine": "duckduckgo-fallback",
                    "verification_detected": True,
                    "results": result_payload,
                    "raw": json.dumps(result_payload),
                }
            browser.close()
            return {
                "ok": False,
                "query": query,
                "engine": "google",
                "verification_detected": True,
                "error": "Google verification page detected; fallback engine not configured.",
            }

        result_payload = page.evaluate(
            """
            () => {
              const nodes = Array.from(document.querySelectorAll('div.g'));
              const top = nodes.slice(0, 5).map((n) => {
                const a = n.querySelector('a');
                const h3 = n.querySelector('h3');
                return {
                  title: h3 ? h3.innerText : '',
                  url: a ? a.href : ''
                };
              }).filter((x) => x.title && x.url);
              return {
                page_title: document.title,
                current_url: location.href,
                top_results: top
              };
            }
            """
        )
        browser.close()
        return {
            "ok": True,
            "query": query,
            "engine": "google",
            "verification_detected": False,
            "manual_verification_used": False,
            "results": result_payload,
            "raw": json.dumps(result_payload),
        }


def browser_google_collect_results(
    query: str,
    pages: int = 3,
    headless: bool = False,
    timeout_ms: int = 20_000,
    wait_for_user_on_verification: bool = True,
    manual_wait_timeout_sec: int = 300,
    verification_poll_interval_sec: int = 5,
) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return {"ok": False, "error": "playwright is not installed"}

    pages = max(1, min(3, int(pages)))

    verification_hints = [
        "unusual traffic",
        "verify you are human",
        "detected unusual traffic",
        "captcha",
        "not a robot",
        "recaptcha",
    ]

    def _is_verification(page: Any) -> bool:
        try:
            title = page.title().lower()
        except Exception:
            title = ""
        try:
            current_url = page.url.lower()
        except Exception:
            current_url = ""
        try:
            body = (page.locator("body").inner_text(timeout=timeout_ms) or "")[:12000].lower()
        except Exception:
            body = ""
        return (
            any(h in body for h in verification_hints)
            or any(h in current_url for h in ["/sorry/", "captcha", "recaptcha", "challenge"])
            or "captcha" in title
            or "verify" in title
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto("https://www.google.com", timeout=timeout_ms)
        page.fill("textarea[name='q']", query, timeout=timeout_ms)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1600)

        if _is_verification(page):
            if wait_for_user_on_verification and not headless:
                deadline = time.time() + max(30, manual_wait_timeout_sec)
                while time.time() < deadline:
                    page.wait_for_timeout(max(1, verification_poll_interval_sec) * 1000)
                    if not _is_verification(page):
                        break
                if _is_verification(page):
                    browser.close()
                    return {
                        "ok": False,
                        "state": "manual_verification_timeout",
                        "query": query,
                        "error": "Timed out waiting for manual verification to complete.",
                    }
            else:
                browser.close()
                return {
                    "ok": False,
                    "state": "manual_verification_required",
                    "query": query,
                    "error": "Google verification detected. Run with headless=false and complete verification manually.",
                }

        all_results: list[dict[str, Any]] = []
        visited_pages: list[str] = []

        for _ in range(pages):
            page.wait_for_timeout(1200)
            visited_pages.append(page.url)
            page_results = page.evaluate(
                """
                () => {
                  const rows = [];
                  const cards = Array.from(document.querySelectorAll('#search .g'));
                  for (const card of cards) {
                    const a = card.querySelector('a');
                    const h3 = card.querySelector('h3');
                    const desc = card.querySelector('div.VwiC3b, div[data-sncf], span.aCOpRe, div[data-content-feature="1"]');
                    const title = h3 ? (h3.innerText || '').trim() : '';
                    const link = a ? (a.href || '').trim() : '';
                    const description = desc ? (desc.innerText || '').trim() : '';
                    const cardText = (card.innerText || '').toLowerCase();
                    const isAd = cardText.includes('sponsored') || cardText.includes('ad ·') || cardText.includes('ads ·');
                    if (title && link) {
                      rows.push({ title, link, description, is_ad: isAd });
                    }
                  }
                  return rows;
                }
                """
            )
            organic = [r for r in page_results if not bool(r.get("is_ad"))]
            for row in organic:
                all_results.append(
                    {
                        "title": str(row.get("title", "")),
                        "link": str(row.get("link", "")),
                        "description": str(row.get("description", "")),
                    }
                )

            next_link = page.locator("a#pnnext")
            if next_link.count() == 0:
                break
            next_link.first.click()

        # Deduplicate by link while preserving order
        deduped: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in all_results:
            link = item["link"]
            if link in seen:
                continue
            seen.add(link)
            deduped.append(item)

        browser.close()
        return {
            "ok": True,
            "query": query,
            "pages_requested": pages,
            "pages_visited": len(visited_pages),
            "visited_urls": visited_pages,
            "results": deduped,
            "count": len(deduped),
        }
