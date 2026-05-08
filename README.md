# Vacatures voor Niels — toolset

Geautomatiseerd scannen van de markt op senior commerciële & leidinggevende
rollen in de houtwereld voor **Niels Hallingse** (CV 2026 leidend). Dagelijks
ophalen via GitHub Actions, scoren op fit met zijn profiel, presenteren in
een Streamlit-dashboard dat online beschikbaar is.

## Wat doet het

1. **Scrapers** halen vacatures op uit drie bronnen:
   - **LinkedIn** (guest-API) — primaire bron, brede dekking, ~40 specifieke
     queries
   - **Bouwjobs.nl** — branchespecifiek bouw, vangt vacatures van houtbedrijven
     die niet altijd op LinkedIn worden gezet
   - **Jobbird.com** — aggregator NL met `?s=` zoek-URL
2. **Scoring** geeft elke vacature een match-score 0–100 op:
   - Rolniveau (vestigingsmanager / commercieel manager / directeur / BD / senior accountmanager)
   - Hout- en bouwbranche-keywords (incl. CV-producten: douglas, vuren,
     grenen, hardhout, plaatmateriaal, thermisch gemodificeerd, verduurzaamd)
   - Bekende hout/bouwmateriaal-bedrijven NL+BE (Jongeneel, Pontmeyer, Stiho,
     Decospan, Lemahieu, Carpentier, etc.)
   - Recruitment-bureaus actief in bouw/industrie (lichte boost)
   - Locatie (Zaanstreek dichtbij Niels' woonplaats Assendelft scoort extra)
   - Vlaanderen (NL-talig BE) telt mee, Wallonië wordt afgestraft
3. **Database** (`data/jobs.db`, SQLite) — dedup op `(source, source_id)`,
   slaat status op (nieuw / interessant / gesolliciteerd / afgewezen) +
   notities.
4. **Dashboard** (`dashboard.py`, Streamlit) — Niels filtert op score, status,
   bron en zoekterm; hij kan status wijzigen en notities maken.

## Profiel (uit CV 2026)

- Niels Hallingse, geboren 1972, woont **Assendelft** (Zaanstreek)
- 25+ jaar in houthandel: Jongeneel → Noord-Europese → Centrop → Callens
  African Woods (BE) → Van de Stadt / Boogaerdt → JenoWood
- **MTS Bouwkunde** + NIMA-A + Specialist Naaldhout (HOC) +
  Senior Executive Management (Krauthammer 2022)
- Talen: NL native, EN professional (geen Duits)
- Specialismen: naaldhout (vuren/grenen/douglas), hardhout, verduurzaamd/
  gecoat hout, thermisch gemodificeerd, plaatmateriaal, bouwmaterialen
- Klantsegmenten: timmerindustrie, houthandel, bouwsector, bouwmaterialenhandel

## Lokaal draaien

```powershell
cd "C:\Users\Tim Luijt\OneDrive - Timesource\5. CLAUDE PROJECTEN\Niels-Vacatures"
pip install -r requirements.txt
python run.py            # alleen NL
python run.py --be       # NL + Vlaanderen (België NL-talig)
streamlit run dashboard.py
```

Dashboard opent op `http://localhost:8501`.

## Online deployen — Streamlit Community Cloud + GitHub Actions

Resultaat: Niels krijgt een URL waar hij in kan loggen met een wachtwoord.
De vacatures worden 's nachts automatisch ververst.

### Eénmalig — repo pushen

```powershell
cd "C:\Users\Tim Luijt\OneDrive - Timesource\5. CLAUDE PROJECTEN\Niels-Vacatures"
git init
git add .
git commit -m "Initial commit"
gh repo create niels-vacatures --private --source=. --push
```

(Of via GitHub.com web UI — maak een private repo, push de code.)

### Streamlit Community Cloud

1. Ga naar **[share.streamlit.io](https://share.streamlit.io)** en log in met
   GitHub.
2. Klik **"New app"** → kies de zojuist aangemaakte repo.
3. Branch: `main`, main file path: `dashboard.py`. Klik **Deploy**.
4. **Settings → Secrets** → plak:
   ```toml
   APP_PASSWORD = "kies-een-wachtwoord"
   ```
   Sla op. App herlaadt automatisch.
5. De app is bereikbaar op `https://<gekozen-naam>.streamlit.app` — deel die
   URL + het wachtwoord met Niels.

### GitHub Actions — dagelijks scrapen

Het workflow-bestand staat al in `.github/workflows/scrape.yml`. Het draait
elke dag om 06:00 UTC en commit de bijgewerkte `data/jobs.db`. Streamlit
Cloud deployt automatisch opnieuw bij elke push.

Eenmalig handmatig testen:

1. GitHub repo → **Actions** tab → "Daily scrape" → **Run workflow**.
2. Na ~5 minuten: zie de nieuwe commit met `chore: dagelijkse vacature-update`.

## Dagelijks lokaal (alternatief, Windows Task Scheduler)

Als je Streamlit Cloud niet wilt, kun je ook lokaal draaien:

1. Open Task Scheduler → **Create Basic Task**
2. Naam: "Niels-Vacatures scraper", Trigger: Daily 07:00
3. Action: **Start a program** — `python.exe`, args `run.py --be`,
   start in: project-map.

## Score-uitleg

| Score | Betekenis                                                     |
|-------|---------------------------------------------------------------|
| 70+   | Zeer goede match (rol klopt + hout-branche of bekend bedrijf) |
| 50–69 | Kijk er naar (rol-niveau klopt, hout-context aannemelijk)     |
| 36–49 | Misschien (vaak te junior of geen hout-context)               |
| ≤ 35  | Filter: vacature heeft geen hout-/branchecontext              |

Het dashboard staat default op een drempel van **50** — Niels ziet de top
matches direct, en kan met de slider lager filteren als hij meer wil zien.

## Bestanden

```
Niels-Vacatures/
├── run.py                       # Daily orchestrator
├── dashboard.py                 # Streamlit-dashboard (entrypoint Cloud)
├── config.py                    # Queries, keywords, hout-bedrijven, profiel
├── scoring.py                   # Match-score (word-boundary keyword match)
├── db.py                        # SQLite-laag
├── scrapers/
│   ├── base.py                  # HTTP-utilities (retry, rate-limit)
│   ├── linkedin.py              # LinkedIn guest-API
│   ├── bouwjobs.py              # Bouwjobs.nl
│   └── jobbird.py               # Jobbird.com NL
├── data/jobs.db                 # SQLite (auto-aangemaakt, gecommit)
├── .github/workflows/scrape.yml # Daily scraper-cron
├── .streamlit/
│   ├── config.toml              # Theme
│   └── secrets.toml.example     # Voorbeeld voor APP_PASSWORD
├── requirements.txt
└── README.md
```

## Aanpassen / uitbreiden

- **Nieuwe zoektermen**: voeg toe aan `QUERIES` (specifiek, voor LinkedIn) of
  `BROAD_QUERIES` (industriebreed, voor Bouwjobs/Jobbird) in `config.py`.
- **Nieuw houtbedrijf bekend?** Voeg toe aan `HOUT_COMPANIES_NL` of
  `HOUT_COMPANIES_BE` — boost van +25 op match.
- **Recruitment-bureau actief in hout/bouw?** Voeg toe aan
  `RECRUITERS_BUILDING` — boost van +10.
- **Score te streng/te los?** Pas waarden aan in `scoring.py`. De cap op 35
  voor vacatures zonder enig hout/branche-signaal voorkomt false positives.

## Bekende beperkingen

- **Indeed.nl** geeft 403 vanaf publieke IP's (ook GitHub Actions). Niet
  haalbaar zonder paid API of headless browser — bewust uitgesloten.
- **Werkzoeken.nl** zoekfunctie is JS-driven, query in URL wordt genegeerd.
- **Nationale Vacaturebank** zit achter DPG-consent gate — vergt cookie-flow
  die we niet automatiseren.
- **Werk.nl (UWV)** is een SPA zonder publieke API.
- LinkedIn-cards bevatten **geen omschrijving** — scoring werkt op titel +
  bedrijfsnaam + locatie. Voor diepere matching zou een tweede pass die
  detail-pagina's ophaalt nodig zijn.

## Mogelijke uitbreidingen (Optie B)

- **Houtbedrijven careers-monitor** — direct polling van Jongeneel,
  Pontmeyer, Stiho, Decospan, Lemahieu careers-pagina's met change-detection.
  Vangt vacatures die niet op LinkedIn/Bouwjobs/Jobbird verschijnen.
- **AI-scoring via Claude API** — laat Claude per vacature beoordelen of
  Niels' CV-historie past, met 1-zin onderbouwing.
- **Dagelijkse e-mail digest** met top-5 nieuwe matches per dag.
- **Headless browser-scraper** voor Indeed/Werkzoeken (Playwright).
