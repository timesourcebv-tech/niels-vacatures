"""Adzuna API scraper — vacature-aggregator vergelijkbaar met Google for Jobs.

Gebruikt de gratis Adzuna API (https://developer.adzuna.com/).
Vereist env vars `ADZUNA_APP_ID` en `ADZUNA_APP_KEY`. Als die ontbreken,
slaat de scraper zichzelf over (graceful skip).

API: https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
"""
from __future__ import annotations

import logging
import os
import time

import requests

from config import REQUEST_DELAY_SECONDS, REQUEST_TIMEOUT, USER_AGENT

log = logging.getLogger(__name__)

ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs"


def scrape_adzuna(
    query: str,
    location: str = "nederland",
    max_results: int = 50,
) -> list[dict]:
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        log.warning("ADZUNA_APP_ID / ADZUNA_APP_KEY niet gezet — Adzuna overgeslagen")
        return []

    region = (location or "nederland").lower()
    country = "be" if region in ("vlaanderen", "belgium", "belgië", "belgie") else "nl"

    results: list[dict] = []
    seen: set[str] = set()
    page = 1
    per_page = 50

    while len(results) < max_results and page <= 5:
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "what": query,
            "results_per_page": per_page,
            "page": page,
            "max_days_old": 30,
            "content-type": "application/json",
        }
        try:
            time.sleep(REQUEST_DELAY_SECONDS)
            resp = requests.get(
                f"{ADZUNA_BASE}/{country}/search/{page}",
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as e:
            log.warning("Adzuna request failed (%s, %s): %s", query, country, e)
            break

        if resp.status_code != 200:
            log.warning("Adzuna %s: HTTP %s for '%s'", country, resp.status_code, query)
            break

        try:
            data = resp.json()
        except ValueError:
            log.warning("Adzuna %s: invalid JSON for '%s'", country, query)
            break

        items = data.get("results", [])
        if not items:
            break

        page_count = 0
        for item in items:
            sid = str(item.get("id") or "")
            if not sid or sid in seen:
                continue
            seen.add(sid)

            company_obj = item.get("company") or {}
            location_obj = item.get("location") or {}

            results.append({
                "source": f"adzuna-{country}",
                "source_id": sid,
                "title": (item.get("title") or "")[:200],
                "company": (company_obj.get("display_name") or None) if isinstance(company_obj, dict) else None,
                "location": (location_obj.get("display_name") or None) if isinstance(location_obj, dict) else None,
                "url": item.get("redirect_url", ""),
                "description": (item.get("description") or "")[:600],
                "posted_at": (item.get("created") or "")[:10] or None,
            })
            page_count += 1
            if len(results) >= max_results:
                break

        if page_count == 0 or page_count < per_page:
            break
        page += 1

    log.info("Adzuna-%s '%s': %d hits", country.upper(), query, len(results))
    return results
