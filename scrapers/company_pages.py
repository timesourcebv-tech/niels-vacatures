"""Houtbedrijven careers-pagina monitor.

Parsed werken-bij-pagina's van een curated lijst van NL/BE hout- en
bouwmateriaal-bedrijven. Per pagina zoeken we naar:
  1. JSON-LD JobPosting (Google-standaard, veel bedrijven gebruiken dit)
  2. Fallback: HTML-links naar individuele vacature-detail-pagina's

Vacatures van deze bedrijven zijn per definitie in vakgebied — geen extra
filtering nodig. Wel scoren we ze normaal voor het rolniveau.
"""
from __future__ import annotations

import json
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import http_get

log = logging.getLogger(__name__)

# Curated lijst — NL hout & bouwmateriaal-bedrijven met career-pagina's.
# (URL gokwerk per bedrijf; scraper faalt graceful als URL niet bestaat.)
COMPANY_CAREERS: list[tuple[str, str]] = [
    # Hout-importeurs & -groothandel
    ("Jongeneel", "https://www.jongeneel.nl/werken-bij"),
    ("Pontmeyer", "https://www.pontmeyer.nl/werken-bij-pontmeyer"),
    ("Stiho", "https://werkenbij.stiho.nl/vacatures"),
    ("Bouwmaat", "https://www.bouwmaat.nl/werken-bij"),
    ("Boogaerdt Hout", "https://www.boogaerdt.nl/vacatures"),
    ("Wilbrink", "https://www.wilbrink.nl/vacatures"),
    ("Van de Stadt Houtimport", "https://www.vandestadt.nl/vacatures"),
    ("JenoWood", "https://www.jenowood.nl/vacatures"),
    ("Heuvelman Hout", "https://www.heuvelmanhout.nl/vacatures"),
    ("Houthandel van Aalst", "https://www.vanaalst.nl/vacatures"),
    ("Wijma", "https://www.wijma.com/nl/vacatures"),
    ("Houtland", "https://www.houtland.com/nl/vacatures"),
    ("Verwol", "https://www.verwol.nl/vacatures"),
    ("Carpentier", "https://www.carpentier.be/nl/vacatures"),
    ("Decospan", "https://www.decospan.com/nl/vacatures"),

    # Bouwmaterialen-grossiers
    ("BMN", "https://www.bmn.nl/werken-bij"),
    ("Raab Karcher", "https://www.raabkarcher.nl/werken-bij"),
    ("Bouwcenter", "https://www.bouwcenter.nl/werken-bij"),
    ("Heuts Bouwmaterialen", "https://www.heuts.nl/vacatures"),
    ("Linthorst Bouwmaterialen", "https://www.linthorstbouwmaterialen.nl/vacatures"),

    # Plaatmateriaal & panelen
    ("Trespa", "https://www.trespa.com/nl/over-trespa/vacatures"),
    ("Rockpanel", "https://www.rockpanel.nl/over-ons/vacatures"),
    ("Spano", "https://www.spano.be/nl/jobs"),

    # Deuren, kozijnen, gevel
    ("Berkvens", "https://www.berkvens.nl/werken-bij"),
    ("Skantrae", "https://www.skantrae.nl/werken-bij"),
    ("Weekamp Deuren", "https://www.weekampdeuren.nl/werken-bij"),
    ("Bruynzeel Deuren", "https://www.bruynzeel.com/nl/werken-bij"),
    ("Reynaers", "https://www.reynaers.nl/nl/over-reynaers/vacatures"),

    # Bouwmateriaal-fabrikanten
    ("Wienerberger", "https://www.wienerberger.nl/werken-bij"),
    ("Rockwool", "https://www.rockwool.com/nl/over-ons/werken-bij/vacatures"),
    ("Knauf", "https://www.knauf.nl/werken-bij"),
    ("Saint-Gobain", "https://www.saint-gobain.nl/werken-bij"),
    ("Etex", "https://www.etexgroup.com/nl-nl/careers"),
    ("Royal Mosa", "https://www.mosa.com/nl/over-mosa/werken-bij"),
]


def _extract_jobpostings(soup: BeautifulSoup) -> list[dict]:
    """Pak JSON-LD JobPostings uit een pagina."""
    jobs: list[dict] = []
    for sc in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(sc.string or "")
        except (json.JSONDecodeError, AttributeError, TypeError):
            continue
        candidates = data if isinstance(data, list) else [data]
        for item in candidates:
            if not isinstance(item, dict):
                continue
            t = item.get("@type")
            if t == "JobPosting":
                jobs.append(item)
            elif t == "ItemList":
                for el in item.get("itemListElement", []):
                    inner = el.get("item") if isinstance(el, dict) else None
                    if isinstance(inner, dict) and inner.get("@type") == "JobPosting":
                        jobs.append(inner)
    return jobs


def _job_from_jobposting(jp: dict, company: str, page_url: str) -> dict | None:
    title = jp.get("title")
    if not title:
        return None
    url = jp.get("url") or jp.get("hiringOrganization", {}).get("url")
    if not url:
        identifier = jp.get("identifier")
        if isinstance(identifier, dict):
            url = identifier.get("value")
    if not url:
        url = page_url
    raw_desc = jp.get("description") or ""
    desc = BeautifulSoup(raw_desc, "lxml").get_text(" ", strip=True)[:1500] if raw_desc else None

    # Locatie
    loc_obj = jp.get("jobLocation")
    location = None
    if isinstance(loc_obj, list) and loc_obj:
        loc_obj = loc_obj[0]
    if isinstance(loc_obj, dict):
        addr = loc_obj.get("address")
        if isinstance(addr, dict):
            location = addr.get("addressLocality") or addr.get("addressRegion")

    sid = re.sub(r"[^a-z0-9]+", "-", title.lower())[:80] + "-" + company.lower().replace(" ", "-")

    return {
        "source": "company-pages",
        "source_id": sid[:120],
        "title": title[:200],
        "company": (jp.get("hiringOrganization") or {}).get("name") if isinstance(jp.get("hiringOrganization"), dict) else company,
        "location": location,
        "url": url,
        "description": desc,
        "posted_at": (jp.get("datePosted") or "")[:10] or None,
    }


def _job_from_link(a, company: str, page_url: str) -> dict | None:
    """Fallback: bouw vacature uit een <a>-tag die naar een vacature-detail wijst."""
    href = a.get("href", "")
    if not href:
        return None
    url = urljoin(page_url, href)
    title = a.get_text(" ", strip=True)
    if not title or len(title) < 6:
        return None
    sid = re.sub(r"[^a-z0-9]+", "-", title.lower())[:80] + "-" + company.lower().replace(" ", "-")
    return {
        "source": "company-pages",
        "source_id": sid[:120],
        "title": title[:200],
        "company": company,
        "location": None,
        "url": url.split("#")[0],
        "description": None,
        "posted_at": None,
    }


def scrape_company_pages(
    query: str = "",
    location: str = "",
    max_results: int = 200,
) -> list[dict]:
    """Loop alle career-pagina's, parse JSON-LD JobPostings en fallback links."""
    results: list[dict] = []
    seen: set[str] = set()

    for company, url in COMPANY_CAREERS:
        try:
            resp = http_get(url)
        except Exception as e:
            log.warning("company-pages %s exception: %s", company, e)
            continue
        if not resp:
            log.info("company-pages %s: geen response (%s)", company, url)
            continue

        soup = BeautifulSoup(resp.text, "lxml")

        # Tier 1: JSON-LD JobPostings
        jp_list = _extract_jobpostings(soup)
        for jp in jp_list:
            job = _job_from_jobposting(jp, company, url)
            if job and job["source_id"] not in seen:
                seen.add(job["source_id"])
                results.append(job)

        # Tier 2: fallback — links die naar vacature-detail-pagina's wijzen
        if not jp_list:
            link_selectors = [
                'a[href*="/vacature/"]',
                'a[href*="/vacatures/"]',
                'a[href*="/jobs/"]',
                'a[href*="/job/"]',
                'a[href*="/career/"]',
                'a[href*="/werken-bij/"]',
            ]
            for sel in link_selectors:
                for a in soup.select(sel):
                    href = a.get("href", "")
                    if not href or href.endswith(("/vacatures/", "/vacatures", "/jobs", "/jobs/", "/werken-bij", "/werken-bij/")):
                        continue
                    job = _job_from_link(a, company, url)
                    if job and job["source_id"] not in seen:
                        seen.add(job["source_id"])
                        results.append(job)

        if len(results) >= max_results:
            break

    log.info("Company-pages: %d vacatures van %d bedrijven", len(results), len(COMPANY_CAREERS))
    return results
