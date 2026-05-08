"""Scraper-modules per bron.

Actieve bronnen:
  - LinkedIn (guest-API): brede dekking, primaire bron
  - Bouwjobs.nl: branchespecifiek bouw — vangt vacatures bij houtbedrijven
                 die niet altijd op LinkedIn worden gezet
  - Jobbird: aggregator NL met `?s=` zoek-URL

Niet actief (getest, geblokkeerd / werken niet voor zoekwoord):
  - Indeed.nl (HTTP 403)
  - Werkzoeken.nl (zoekwoord wordt genegeerd in URL)
  - Nationale Vacaturebank (DPG consent gate)
  - Werk.nl (UWV — SPA zonder publieke API)
"""
from .linkedin import scrape_linkedin
from .bouwjobs import scrape_bouwjobs
from .jobbird import scrape_jobbird
from .stepstone import scrape_stepstone
from .adzuna import scrape_adzuna

ALL_SCRAPERS = [
    ("linkedin", scrape_linkedin),
    ("bouwjobs", scrape_bouwjobs),
    ("jobbird", scrape_jobbird),
    ("stepstone", scrape_stepstone),
    ("adzuna", scrape_adzuna),
]
