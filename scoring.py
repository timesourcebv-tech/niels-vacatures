"""Match-score per vacature, gebaseerd op Niels' CV-profiel.

Scorebanden:
  >= 70: zeer goede match (rol + houtbranche of bekend houtbedrijf)
  50-69: kijk er naar (rol klopt, hout-context aannemelijk)
  30-49: misschien (rol klopt, hout-context onzeker)
  < 30: waarschijnlijk irrelevant
"""
from __future__ import annotations

import re

from config import (
    CITIES_BE_NL,
    CITIES_NEAR,
    CITIES_RANDSTAD,
    HIGH_VALUE_TITLE_TERMS,
    HOUT_COMPANIES,
    INDUSTRY_KEYWORDS,
    LEADERSHIP_TERMS,
    NEGATIVE_LOCATIONS_BE,
    NEGATIVE_TERMS,
    POSITIVE_BOOST,
    RECRUITERS_BUILDING,
    ROLE_KEYWORDS,
    STRICT_NEGATIVE_TITLE_SUBSTRINGS,
)


def _word_match(keywords: list[str], text: str) -> bool:
    """Match keyword als heel woord (word boundary) — voorkomt 'hout' in 'schouten'."""
    if not text:
        return False
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE):
            return True
    return False


def score_job(
    title: str,
    description: str | None,
    location: str | None,
    company: str | None = None,
) -> int:
    """Score 0-100."""
    t = (title or "").lower()
    d = (description or "").lower()
    loc = (location or "").lower()
    co = (company or "").lower()

    # Hard exclude — substring-match in titel (operationeel/zorg/etc.)
    if any(sub in t for sub in STRICT_NEGATIVE_TITLE_SUBSTRINGS):
        return 0

    score = 0

    # Rol-niveau
    if _word_match(ROLE_KEYWORDS, t):
        score += 30
        if _word_match(LEADERSHIP_TERMS, t):
            score += 15
    elif _word_match(ROLE_KEYWORDS, d):
        score += 10

    # Extra boost voor doelrol-termen in titel (manager/business/developer/sales/etc.)
    high_value_matches = sum(
        1 for term in HIGH_VALUE_TITLE_TERMS
        if re.search(r"\b" + re.escape(term) + r"\b", t, re.IGNORECASE)
    )
    if high_value_matches:
        score += min(high_value_matches * 10, 30)

    # Industrie / hout — woordgrenzen verplicht
    industry_in_title = _word_match(INDUSTRY_KEYWORDS, t)
    industry_in_company = _word_match(INDUSTRY_KEYWORDS, co)
    industry_in_desc = _word_match(INDUSTRY_KEYWORDS, d)
    company_is_houtbedrijf = _word_match(HOUT_COMPANIES, co)

    if industry_in_title:
        score += 35
    elif industry_in_company:
        score += 30
    elif industry_in_desc:
        score += 20

    if company_is_houtbedrijf:
        score += 25

    has_industry_signal = (
        industry_in_title or industry_in_company
        or industry_in_desc or company_is_houtbedrijf
    )

    # Recruiter actief in bouw/industrie
    if _word_match(RECRUITERS_BUILDING, co):
        score += 10

    # Positieve termen
    if _word_match(POSITIVE_BOOST, f"{t} {d} {co}"):
        score += 8

    # Locatie
    if any(c in loc for c in CITIES_NEAR):
        score += 12
    elif any(c in loc for c in CITIES_RANDSTAD):
        score += 8
    elif any(c in loc for c in CITIES_BE_NL):
        score += 6
    elif "nederland" in loc or "netherlands" in loc:
        score += 5
    elif any(c in loc for c in ["belgium", "belgië", "vlaanderen", "flanders"]):
        score += 4

    # Negatief
    if _word_match(NEGATIVE_TERMS, t):
        score -= 40
    elif _word_match(NEGATIVE_TERMS, d[:500]):
        score -= 15
    if any(neg in loc for neg in NEGATIVE_LOCATIONS_BE):
        score -= 30

    # Geen vakgebied-signaal in titel, bedrijf én beschrijving → niet relevant.
    # Vacature komt niet in DB (run.py filtert op score >= 25 + cleanup
    # verwijdert score < 25).
    if not has_industry_signal:
        return 0

    return max(0, min(100, score))
