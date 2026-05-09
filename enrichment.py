"""Enrichment: vacature-omschrijving ophalen via JSON-LD JobPosting.

LinkedIn, Jobbird, StepStone en de meeste publieke job-platforms embedden
een `<script type="application/ld+json">` met `@type: JobPosting`. We pakken
daaruit het `description`-veld en strippen HTML naar platte tekst.

Beperkt tot N records per run om binnen de cron-runtime te blijven.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from bs4 import BeautifulSoup

from db import get_conn
from scrapers.base import http_get

log = logging.getLogger(__name__)


def _extract_jobposting_description(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")
    for sc in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(sc.string or "")
        except (json.JSONDecodeError, AttributeError, TypeError):
            continue
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("@type") == "JobPosting":
                    data = item
                    break
        if isinstance(data, dict) and data.get("@type") == "JobPosting":
            raw = data.get("description") or ""
            if raw:
                text = BeautifulSoup(raw, "lxml").get_text(" ", strip=True)
                if text:
                    return text
    # Fallback: og:description / meta description
    for selector in [
        ('meta', {"property": "og:description"}),
        ('meta', {"name": "description"}),
    ]:
        meta = soup.find(*selector)
        if meta and meta.get("content"):
            content = meta.get("content").strip()
            if len(content) > 50:
                return content
    return None


def fetch_description(url: str) -> Optional[str]:
    if not url:
        return None
    resp = http_get(url)
    if not resp:
        return None
    return _extract_jobposting_description(resp.text)


def enrich_descriptions(limit: int = 200, min_score: int = 30) -> dict:
    """Verrijk vacatures zonder description, top-score eerst.

    Returns dict met `attempted`, `enriched`, `failed`.
    """
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, url FROM jobs
            WHERE (description IS NULL OR description = '')
              AND score >= ?
              AND url IS NOT NULL AND url != ''
            ORDER BY score DESC, discovered_at DESC
            LIMIT ?
            """,
            (min_score, limit),
        ).fetchall()

    attempted = len(rows)
    enriched = 0
    failed = 0

    for r in rows:
        desc = None
        try:
            desc = fetch_description(r["url"])
        except Exception as e:
            log.warning("Enrichment fout %s: %s", r["url"][:80], e)

        if desc:
            with get_conn() as conn:
                conn.execute(
                    "UPDATE jobs SET description = ? WHERE id = ?",
                    (desc[:1500], r["id"]),
                )
            enriched += 1
        else:
            failed += 1

    log.info(
        "Enrichment: %d attempted, %d enriched, %d failed (score >= %d)",
        attempted, enriched, failed, min_score,
    )
    return {"attempted": attempted, "enriched": enriched, "failed": failed}


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    enrich_descriptions(limit=200, min_score=30)
