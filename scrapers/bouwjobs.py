"""Bouwjobs.nl scraper — branchespecifiek voor de bouwbranche.

Bouwjobs is een groot bouwsector-vacatureplatform (gelinkt aan Bouwwereld).
We gebruiken hun publieke zoek-URL (?s=) en parsen de resultaten.
"""
from __future__ import annotations

import logging
import re
from bs4 import BeautifulSoup
from .base import http_get

log = logging.getLogger(__name__)

BOUWJOBS_BASE = "https://www.bouwjobs.nl/"


def _extract_id(url: str) -> str:
    m = re.search(r"/vacature/([^/?#]+)", url)
    return m.group(1) if m else url


def scrape_bouwjobs(query: str, location: str = "", max_results: int = 50) -> list[dict]:
    results: list[dict] = []
    seen: set[str] = set()

    page = 1
    while len(results) < max_results and page <= 5:
        params = {"s": query}
        if page > 1:
            params["page"] = page
        resp = http_get(BOUWJOBS_BASE, params=params)
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
                href = "https://www.bouwjobs.nl" + href
            if "/vacature/" not in href:
                continue

            sid = _extract_id(href)
            if sid in seen:
                continue
            seen.add(sid)

            container = a
            for _ in range(4):
                if container.parent:
                    container = container.parent
                if container.name in ("article", "li", "div") and len(container.get_text(strip=True)) > 30:
                    break

            text = container.get_text(" ", strip=True)
            title_el = a.select_one("h2, h3, .title, .job-title, span")
            title = title_el.get_text(strip=True) if title_el and title_el.get_text(strip=True) else a.get_text(" ", strip=True)
            if not title or len(title) < 4:
                continue

            company = None
            for cls in ["company", "employer", "bedrijfsnaam", "company-name"]:
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
                "source": "bouwjobs",
                "source_id": sid,
                "title": title[:200],
                "company": company,
                "location": loc_text,
                "url": href.split("?")[0],
                "description": text[:400] if text else None,
                "posted_at": None,
            })
            page_count += 1
            if len(results) >= max_results:
                break

        if page_count == 0:
            break
        page += 1

    log.info("Bouwjobs '%s' (%s): %d hits", query, location, len(results))
    return results
