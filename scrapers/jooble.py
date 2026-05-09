"""Jooble API scraper — wereldwijde vacature-aggregator (NL + BE).

Documentatie: https://jooble.org/api/about
Endpoint: POST https://{country}.jooble.org/api/{api_key}
Body: {"keywords": "...", "location": "...", "page": "1"}

Vereist env var `JOOBLE_API_KEY`. Skipt graceful als die mist.
"""
from __future__ import annotations

import json
import logging
import os
import time

import requests

from config import REQUEST_DELAY_SECONDS, REQUEST_TIMEOUT, USER_AGENT

log = logging.getLogger(__name__)


def scrape_jooble(
    query: str,
    location: str = "nederland",
    max_results: int = 50,
) -> list[dict]:
    api_key = os.environ.get("JOOBLE_API_KEY")
    if not api_key:
        log.warning("JOOBLE_API_KEY ontbreekt — Jooble overgeslagen")
        return []

    region = (location or "nederland").lower()
    is_be = region in ("vlaanderen", "belgium", "belgië", "belgie", "antwerpen", "gent", "brugge")
    where = "Belgium" if is_be else "Netherlands"
    src_label = "be" if is_be else "nl"

    # Global endpoint — country-subdomains geven 403 met onze key.
    endpoint = f"https://jooble.org/api/{api_key}"
    expected_loc_terms = (
        ["belgium", "belgië", "belgie", "vlaanderen", "antwerp", "gent", "brugge", "kortrijk", "leuven", "hasselt"]
        if is_be else
        ["netherlands", "nederland", " nl"]
    )
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    results: list[dict] = []
    seen: set[str] = set()
    page = 1
    while len(results) < max_results and page <= 5:
        body = {
            "keywords": query,
            "location": where,
            "page": str(page),
            "ResultOnPage": "20",
        }
        try:
            time.sleep(REQUEST_DELAY_SECONDS)
            resp = requests.post(
                endpoint, headers=headers,
                data=json.dumps(body), timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as e:
            log.warning("Jooble %s '%s' request failed: %s", subdomain, query, e)
            break

        if resp.status_code != 200:
            log.warning("Jooble %s: HTTP %s for '%s'", subdomain, resp.status_code, query)
            break

        try:
            data = resp.json()
        except ValueError:
            log.warning("Jooble %s: invalid JSON for '%s'", subdomain, query)
            break

        items = data.get("jobs") or []
        if not items:
            break

        page_count = 0
        for item in items:
            url = item.get("link") or ""
            if not url:
                continue
            loc_str = (item.get("location") or "").lower()
            # Skip vacatures buiten NL/BE (Jooble returneert wereldwijd zonder strikt filter)
            if not any(t in loc_str for t in expected_loc_terms):
                continue

            sid = url.split("?")[0].rstrip("/").split("/")[-1] or url
            if sid in seen:
                continue
            seen.add(sid)

            results.append({
                "source": f"jooble-{src_label}",
                "source_id": sid,
                "title": (item.get("title") or "")[:200],
                "company": item.get("company") or None,
                "location": item.get("location") or where,
                "url": url,
                "description": (item.get("snippet") or "")[:600] or None,
                "posted_at": (item.get("updated") or "")[:10] or None,
            })
            page_count += 1
            if len(results) >= max_results:
                break

        if page_count == 0:
            break
        page += 1

    log.info("Jooble-%s '%s': %d hits", src_label.upper(), query, len(results))
    return results
