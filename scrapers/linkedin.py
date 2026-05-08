"""LinkedIn Jobs guest-API scraper.

Gebruikt de publieke 'seeMoreJobPostings' endpoint die LinkedIn voor niet-ingelogde
gebruikers serveert. Geen authenticatie nodig.
"""
from __future__ import annotations

import logging
import re
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup
from .base import http_get

log = logging.getLogger(__name__)

LINKEDIN_GUEST_URL = (
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
)


def _clean_url(url: str) -> str:
    """Strip tracking-querystrings, behoud pad + jobId."""
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def _extract_job_id(url: str) -> str | None:
    m = re.search(r"/view/(?:[^/]+-)?(\d+)", url)
    if m:
        return m.group(1)
    m = re.search(r"currentJobId=(\d+)", url)
    return m.group(1) if m else None


def scrape_linkedin(query: str, location: str = "Netherlands", max_results: int = 50) -> list[dict]:
    results: list[dict] = []
    seen_ids: set[str] = set()
    start = 0
    page_size = 25

    while start < max_results:
        params = {
            "keywords": query,
            "location": location,
            "f_TPR": "r2592000",
            "start": start,
        }
        resp = http_get(LINKEDIN_GUEST_URL, params=params)
        if not resp or not resp.text.strip():
            break

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select("li, div.base-card")
        if not cards:
            break

        page_count = 0
        for card in cards:
            title_el = card.select_one(".base-search-card__title, h3.base-search-card__title")
            link_el = card.select_one("a.base-card__full-link, a.base-search-card__media-link")
            if not link_el:
                link_el = card.select_one("a[href*='/jobs/view/']")
            if not title_el or not link_el:
                continue

            url = _clean_url(link_el.get("href", ""))
            job_id = _extract_job_id(url)
            if not job_id or job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            company_el = card.select_one(".base-search-card__subtitle a, h4.base-search-card__subtitle")
            location_el = card.select_one(".job-search-card__location")
            time_el = card.select_one("time")

            results.append({
                "source": "linkedin",
                "source_id": job_id,
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else None,
                "location": location_el.get_text(strip=True) if location_el else location,
                "url": url,
                "description": None,
                "posted_at": time_el.get("datetime") if time_el else None,
            })
            page_count += 1
            if len(results) >= max_results:
                break

        if page_count == 0:
            break
        start += page_size

    log.info("LinkedIn '%s' (%s): %d hits", query, location, len(results))
    return results
