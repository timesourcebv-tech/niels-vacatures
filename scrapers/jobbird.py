"""Jobbird.com NL scraper.

Gebruikt hun publieke search-URL met `?s=` parameter (uit het zoekformulier).
"""
from __future__ import annotations

import logging
import re
from bs4 import BeautifulSoup
from .base import http_get

log = logging.getLogger(__name__)

JOBBIRD_SEARCH = "https://www.jobbird.com/nl/vacature"


def _extract_id(url: str) -> str:
    m = re.search(r"/vacature/(\d+)", url)
    return m.group(1) if m else url


def scrape_jobbird(query: str, location: str = "", max_results: int = 50) -> list[dict]:
    results: list[dict] = []
    seen: set[str] = set()

    page = 1
    while len(results) < max_results and page <= 5:
        params = {"s": query}
        if page > 1:
            params["p"] = page
        resp = http_get(JOBBIRD_SEARCH, params=params)
        if not resp:
            break
        soup = BeautifulSoup(resp.text, "lxml")

        cards = soup.select('a[href*="/vacature/"]')
        if not cards:
            break

        page_count = 0
        for a in cards:
            href = a.get("href", "")
            if not href.startswith("http"):
                href = "https://www.jobbird.com" + href
            if "/vacature/" not in href or href.endswith("/vacature"):
                continue

            sid = _extract_id(href)
            if sid in seen or sid == href:
                continue
            seen.add(sid)

            container = a
            for _ in range(4):
                if container.parent:
                    container = container.parent
                if container.name in ("article", "li", "div") and len(container.get_text(strip=True)) > 30:
                    break

            title_el = a.select_one("h2, h3, .title, .job-title, span")
            title = title_el.get_text(strip=True) if title_el and title_el.get_text(strip=True) else a.get_text(" ", strip=True)
            if not title or len(title) < 4 or title.lower() in ("solliciteer", "bekijk vacature"):
                continue

            company = None
            for cls in ["company", "employer", "bedrijf"]:
                el = container.select_one(f"[class*='{cls}']")
                if el:
                    company = el.get_text(strip=True)
                    break

            loc_text = location or "Nederland"
            for cls in ["location", "plaats", "regio", "city"]:
                el = container.select_one(f"[class*='{cls}']")
                if el:
                    loc_text = el.get_text(strip=True)
                    break

            results.append({
                "source": "jobbird",
                "source_id": sid,
                "title": title[:200],
                "company": company,
                "location": loc_text,
                "url": href.split("?")[0],
                "description": None,
                "posted_at": None,
            })
            page_count += 1
            if len(results) >= max_results:
                break

        if page_count == 0:
            break
        page += 1

    log.info("Jobbird '%s' (%s): %d hits", query, location, len(results))
    return results
