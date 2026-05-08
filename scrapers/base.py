"""Gedeelde HTTP-utilities voor scrapers."""
from __future__ import annotations

import time
import logging
import requests
from config import USER_AGENT, REQUEST_TIMEOUT, REQUEST_DELAY_SECONDS

log = logging.getLogger(__name__)


def http_get(url: str, params: dict | None = None, retries: int = 2) -> requests.Response | None:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    last_err = None
    for attempt in range(retries + 1):
        try:
            time.sleep(REQUEST_DELAY_SECONDS)
            resp = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp
            if resp.status_code in (429, 503):
                wait = (attempt + 1) * 5
                log.warning("Rate limited (%s) on %s, wachten %ss", resp.status_code, url, wait)
                time.sleep(wait)
                continue
            log.warning("HTTP %s op %s", resp.status_code, url)
            return None
        except requests.RequestException as e:
            last_err = e
            log.warning("Fout bij %s (poging %d): %s", url, attempt + 1, e)
            time.sleep(2 * (attempt + 1))
    log.error("Definitief gefaald: %s (%s)", url, last_err)
    return None
