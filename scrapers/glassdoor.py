"""Glassdoor NL + BE scraper.

URL: https://www.glassdoor.{nl|be}/Job/jobs.htm?sc.keyword={query}
Cards via [data-test="jobListing"] met sub-elementen voor titel/locatie/etc.
"""
from __future__ import annotations

import logging
import re
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from .base import http_get

log = logging.getLogger(__name__)


def _clean_company(text: str) -> str:
    """Strip rating-suffix uit bedrijfsnaam (bv 'Hays3,6' → 'Hays')."""
    return re.sub(r"\d[\d,.]*$", "", text).strip()


def _resolve_url(href: str, base: str) -> str:
    if not href:
        return ""
    if href.startswith("http"):
        return href.split("?")[0]
    return base + href.split("?")[0]


def scrape_glassdoor(
    query: str,
    location: str = "nederland",
    max_results: int = 50,
) -> list[dict]:
    region = (location or "nederland").lower()
    is_be = region in ("vlaanderen", "belgium", "belgië", "belgie", "antwerpen", "gent", "brugge")
    domain = "be" if is_be else "nl"
    src_label = "be" if is_be else "nl"
    base = f"https://www.glassdoor.{domain}"

    params = {"sc.keyword": query}
    url = f"{base}/Job/jobs.htm?{urlencode(params)}"

    resp = http_get(url)
    if not resp:
        log.info("Glassdoor-%s '%s': 0 hits (no response)", src_label.upper(), query)
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    cards = soup.select('li[data-test="jobListing"]')

    results: list[dict] = []
    seen: set[str] = set()
    for card in cards:
        title_el = card.select_one('[data-test="job-title"]')
        if not title_el:
            continue
        title = title_el.get_text(" ", strip=True)
        if not title:
            continue

        link_el = card.select_one('a[data-test="job-link"]')
        href = _resolve_url(link_el.get("href", "") if link_el else "", base)
        if not href:
            continue

        # ID uit href (pos-param of unique slug)
        m = re.search(r"jobListingId=(\d+)|/job/[^/]+-([A-Z0-9]+)\.htm|pos=(\d+)", href)
        sid = (m.group(1) or m.group(2) or m.group(3)) if m else None
        if not sid:
            sid = title + (link_el.get("href", "")[:50] if link_el else "")
        if sid in seen:
            continue
        seen.add(sid)

        # Company — meerdere mogelijke selectors
        company = None
        for sel in [
            '[data-test="employer-name"]',
            'a[href*="/Reviews/"]',
            'a[href*="/Overview/"]',
            '[class*="employer-name"]',
            '[class*="EmployerProfile"]',
        ]:
            co_el = card.select_one(sel)
            if co_el:
                company = _clean_company(co_el.get_text(" ", strip=True))
                if company:
                    break

        loc_el = card.select_one('[data-test="emp-location"]')
        snippet_el = card.select_one('[data-test="descSnippet"]')
        age_el = card.select_one('[data-test="job-age"]')

        results.append({
            "source": f"glassdoor-{src_label}",
            "source_id": str(sid),
            "title": title[:200],
            "company": company or None,
            "location": loc_el.get_text(strip=True) if loc_el else region.title(),
            "url": href,
            "description": snippet_el.get_text(" ", strip=True)[:400] if snippet_el else None,
            "posted_at": age_el.get_text(strip=True) if age_el else None,
        })
        if len(results) >= max_results:
            break

    log.info("Glassdoor-%s '%s': %d hits", src_label.upper(), query, len(results))
    return results
