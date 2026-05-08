"""StepStone NL + BE scraper.

URL-patronen:
  NL:   https://www.stepstone.nl/vacatures/{slug}/in-{region}
  BE:   https://www.stepstone.be/jobs/{slug}/in-{region}

We gebruiken `[data-at="job-item"]` voor de cards en de inline href
`/jobs--...-{jobId}-inline.html` voor unieke ID's.
"""
from __future__ import annotations

import logging
import re
from bs4 import BeautifulSoup
from .base import http_get

log = logging.getLogger(__name__)


def _slug(query: str) -> str:
    return re.sub(r"\s+", "-", query.strip().lower())


def _extract_id(href: str) -> str | None:
    m = re.search(r"-(\d{4,})(?:-inline)?\.html", href)
    return m.group(1) if m else None


def scrape_stepstone(
    query: str,
    location: str = "nederland",
    max_results: int = 50,
) -> list[dict]:
    region = (location or "nederland").lower()
    is_be = region in ("vlaanderen", "belgium", "belgië", "belgie", "antwerpen", "gent", "brugge")
    base = "https://www.stepstone.be/jobs" if is_be else "https://www.stepstone.nl/vacatures"
    region_slug = "vlaanderen" if is_be else "nederland"

    results: list[dict] = []
    seen: set[str] = set()
    page = 1
    while len(results) < max_results and page <= 5:
        url = f"{base}/{_slug(query)}/in-{region_slug}"
        if page > 1:
            url += f"?action=paging_next&page={page}"
        resp = http_get(url)
        if not resp:
            break

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select('[data-at="job-item"]')
        if not cards:
            break

        page_count = 0
        for card in cards:
            title_el = card.select_one('[data-at="job-item-title"]')
            if not title_el:
                continue
            href = title_el.get("href", "")
            if not href.startswith("http"):
                href = ("https://www.stepstone.be" if is_be else "https://www.stepstone.nl") + href

            sid = _extract_id(href)
            if not sid or sid in seen:
                continue
            seen.add(sid)

            company_el = card.select_one('[data-at="job-item-company-name"]')
            location_el = card.select_one('[data-at="job-item-location"]')

            results.append({
                "source": "stepstone-be" if is_be else "stepstone-nl",
                "source_id": sid,
                "title": title_el.get_text(" ", strip=True)[:200],
                "company": company_el.get_text(" ", strip=True) if company_el else None,
                "location": location_el.get_text(" ", strip=True) if location_el else region.title(),
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

    log.info("StepStone-%s '%s': %d hits", "BE" if is_be else "NL", query, len(results))
    return results
