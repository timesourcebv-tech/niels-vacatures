"""Daily orchestrator. Draait alle scrapers, scoort en slaat op in SQLite.

Gebruik:
  python run.py            # alleen NL
  python run.py --be       # NL + Vlaanderen
"""
from __future__ import annotations

import logging
import sys

from config import BROAD_QUERIES, MAX_RESULTS_PER_QUERY, QUERIES
from db import stats, upsert_jobs
from enrichment import enrich_descriptions
from scoring import score_job
from scrapers import (
    scrape_adzuna,
    scrape_bouwjobs,
    scrape_company_pages,
    scrape_glassdoor,
    scrape_jobbird,
    scrape_jooble,
    scrape_linkedin,
    scrape_stepstone,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("run")


def _score(jobs: list[dict]) -> None:
    for j in jobs:
        j["score"] = score_job(
            title=j.get("title", ""),
            description=j.get("description"),
            location=j.get("location"),
            company=j.get("company"),
        )


def run_once(include_belgium: bool = False) -> dict:
    all_jobs: list[dict] = []

    # LinkedIn — specifieke queries × locatie(s)
    linkedin_locs = ["Netherlands"]
    if include_belgium:
        linkedin_locs.append("Belgium")
    for loc in linkedin_locs:
        for q in QUERIES:
            try:
                jobs = scrape_linkedin(q, loc, max_results=MAX_RESULTS_PER_QUERY)
                _score(jobs)
                all_jobs.extend(jobs)
            except Exception as e:
                log.exception("LinkedIn '%s' (%s) failed: %s", q, loc, e)

    # Bouwjobs — branchespecifiek, brede industrie-queries
    for q in BROAD_QUERIES:
        try:
            jobs = scrape_bouwjobs(q, max_results=MAX_RESULTS_PER_QUERY)
            _score(jobs)
            all_jobs.extend(jobs)
        except Exception as e:
            log.exception("Bouwjobs '%s' failed: %s", q, e)

    # Jobbird — aggregator, brede industrie-queries
    for q in BROAD_QUERIES:
        try:
            jobs = scrape_jobbird(q, max_results=MAX_RESULTS_PER_QUERY)
            _score(jobs)
            all_jobs.extend(jobs)
        except Exception as e:
            log.exception("Jobbird '%s' failed: %s", q, e)

    # StepStone — NL + BE (Vlaanderen) als include_belgium
    stepstone_locs = ["nederland"]
    if include_belgium:
        stepstone_locs.append("vlaanderen")
    for loc in stepstone_locs:
        for q in BROAD_QUERIES:
            try:
                jobs = scrape_stepstone(q, location=loc, max_results=MAX_RESULTS_PER_QUERY)
                _score(jobs)
                all_jobs.extend(jobs)
            except Exception as e:
                log.exception("StepStone '%s' (%s) failed: %s", q, loc, e)

    # Adzuna API — aggregator (Google-for-Jobs achtige dekking)
    adzuna_locs = ["nederland"]
    if include_belgium:
        adzuna_locs.append("vlaanderen")
    for loc in adzuna_locs:
        for q in BROAD_QUERIES:
            try:
                jobs = scrape_adzuna(q, location=loc, max_results=MAX_RESULTS_PER_QUERY)
                _score(jobs)
                all_jobs.extend(jobs)
            except Exception as e:
                log.exception("Adzuna '%s' (%s) failed: %s", q, loc, e)

    # Jooble API — extra wereldwijde aggregator
    jooble_locs = ["nederland"]
    if include_belgium:
        jooble_locs.append("vlaanderen")
    for loc in jooble_locs:
        for q in BROAD_QUERIES:
            try:
                jobs = scrape_jooble(q, location=loc, max_results=MAX_RESULTS_PER_QUERY)
                _score(jobs)
                all_jobs.extend(jobs)
            except Exception as e:
                log.exception("Jooble '%s' (%s) failed: %s", q, loc, e)

    # Glassdoor — NL + BE
    glassdoor_locs = ["nederland"]
    if include_belgium:
        glassdoor_locs.append("vlaanderen")
    for loc in glassdoor_locs:
        for q in BROAD_QUERIES:
            try:
                jobs = scrape_glassdoor(q, location=loc, max_results=MAX_RESULTS_PER_QUERY)
                _score(jobs)
                all_jobs.extend(jobs)
            except Exception as e:
                log.exception("Glassdoor '%s' (%s) failed: %s", q, loc, e)

    # Company-pages — directe werken-bij van top hout/bouw-bedrijven (1x per run)
    try:
        jobs = scrape_company_pages()
        _score(jobs)
        all_jobs.extend(jobs)
    except Exception as e:
        log.exception("Company-pages failed: %s", e)

    log.info("Totaal opgehaald: %d", len(all_jobs))

    relevant = [j for j in all_jobs if j["score"] >= 25]
    log.info("Relevant (score >= 25): %d", len(relevant))

    inserted, skipped = upsert_jobs(relevant)
    log.info("Opgeslagen: %d nieuw, %d bekend (score geüpdatet)", inserted, skipped)

    # Cleanup: gooi vacatures weg die door scoring-updates onder de drempel zijn
    # gevallen (bv. nieuwe negative-terms). Houdt DB schoon en dashboard relevant.
    from db import get_conn as _gc
    with _gc() as conn:
        purged = conn.execute("DELETE FROM jobs WHERE score < 25").rowcount
        if purged:
            log.info("Cleanup: %d niet-relevante vacatures verwijderd uit DB", purged)

    # Enrichment: ophalen van vacature-omschrijvingen via JSON-LD JobPosting
    # (LinkedIn/Jobbird/StepStone-cards bevatten geen description in zoekresultaten)
    enrich_stats = enrich_descriptions(limit=200, min_score=30)
    log.info("Enrichment-resultaat: %s", enrich_stats)

    s = stats()
    log.info(
        "DB-status: %s totaal | %s nieuw | %s interessant | %s gesolliciteerd",
        s.get("total"), s.get("new_count"),
        s.get("interesting_count"), s.get("applied_count"),
    )
    return {"fetched": len(all_jobs), "stored": inserted, "stats": s}


if __name__ == "__main__":
    include_be = "--be" in sys.argv or "--belgium" in sys.argv
    run_once(include_belgium=include_be)
