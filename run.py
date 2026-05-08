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
from scoring import score_job
from scrapers import scrape_bouwjobs, scrape_jobbird, scrape_linkedin

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

    log.info("Totaal opgehaald: %d", len(all_jobs))

    relevant = [j for j in all_jobs if j["score"] >= 25]
    log.info("Relevant (score >= 25): %d", len(relevant))

    inserted, skipped = upsert_jobs(relevant)
    log.info("Opgeslagen: %d nieuw, %d bekend (score geüpdatet)", inserted, skipped)

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
