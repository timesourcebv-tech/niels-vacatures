"""Centrale configuratie: zoekqueries, filters, scoring-keywords.

Gebaseerd op CV Niels Hallingse 2026 — bij twijfel is het CV leidend.
"""
from __future__ import annotations

# ──────────────────────────────────────────────────────────
# Profiel — gebaseerd op CV (leidend bij twijfel)
# ──────────────────────────────────────────────────────────
NIELS_PROFILE = {
    "name": "Niels Hallingse",
    "born": "1972-06-19",
    "location": "Assendelft (Zaanstreek)",
    "experience_years": 25,
    "languages": ["NL native", "EN professional"],
    "education": [
        "MTS Bouwkunde (1989-1993)",
        "NIMA-A Sales (2002, 2007)",
        "Specialist Naaldhout — HOC (2007)",
        "Senior Executive Management — Krauthammer (2022)",
    ],
    "specialties": [
        "naaldhout (vuren, grenen, douglas)",
        "hardhout / Afrikaans hardhout",
        "verduurzaamd / gecoat hout",
        "thermisch gemodificeerd hout",
        "plaatmaterialen",
        "bouwmaterialen",
        "houtimport en logistiek",
        "verkoop en accountmanagement",
        "leidinggevend / vestigings- en commercieel management",
    ],
    "customer_segments": [
        "timmerindustrie",
        "houthandelaren",
        "bouwsector",
        "bouwmaterialenhandel",
    ],
    "career_history": [
        "Jongeneel (1999-2007)",
        "Noord-Europese Houtimport (2007-2011)",
        "Centrop Houtimport (2011-2016)",
        "Callens African Woods, BE (2016-2019)",
        "Van de Stadt Houtimport / Boogaerdt (2019-2024) — Vestigingsmanager",
        "JenoWood (2024-heden) — Nationaal Accountmanager",
    ],
}

# ──────────────────────────────────────────────────────────
# Rolniveau — leidinggevend / senior commercieel of hoger
# ──────────────────────────────────────────────────────────
ROLE_KEYWORDS = [
    # Leidinggevend
    "vestigingsmanager", "vestiging manager", "branch manager",
    "bedrijfsleider", "operationeel manager", "operations manager",
    "commercieel manager", "commercieel directeur", "sales director",
    "sales manager", "salesmanager", "manager sales",
    "country manager", "general manager", "managing director",
    "directeur", "directie", "algemeen directeur",
    "regio manager", "regiomanager", "regional manager",
    "hoofd verkoop", "hoofd commercie", "head of sales",
    # Senior commercieel
    "senior accountmanager", "senior account manager",
    "key accountmanager", "key account manager",
    "national account manager", "nationaal accountmanager",
    "business development manager", "business development",
    "sr. accountmanager", "senior salesmanager",
    "specialist accountmanager",
    "commercieel adviseur senior",
    # Inkoop/sales op senior niveau
    "category manager", "product manager",
    "key account director", "sales lead",
]

LEADERSHIP_TERMS = [
    "vestigingsmanager", "bedrijfsleider", "commercieel manager",
    "commercieel directeur", "directeur", "country manager",
    "general manager", "branch manager", "operationeel manager",
    "operations manager", "sales director", "salesdirecteur",
    "managing director", "algemeen directeur", "regiomanager",
    "regio manager", "head of", "hoofd ",
    "manager",  # losstaande "Manager" in titel telt als leadership
    "director", "lead", "chief",
]

# ──────────────────────────────────────────────────────────
# Industrie — hout en aanpalende bouwbranche (uit CV)
# ──────────────────────────────────────────────────────────
INDUSTRY_KEYWORDS = [
    # Hout algemeen
    "hout", "houtimport", "houthandel", "houtbewerking",
    "houtindustrie", "houtproducten", "houtbranche",
    "timber", "wood", "lumber",
    # Hout-compound termen (die niet matchen via word-boundary 'hout')
    "houtzagerij", "houtmolen", "houtmagazijn", "houtopslag",
    "houttoeleverancier", "houtleverancier", "houtveredeling",
    "houtskeletbouw", "houtland", "houtfabriek", "houtproductie",
    "houtdistributie", "houtgroothandel", "houtdetailhandel",
    "houtbedrijf", "houtmarkt", "houtbouw", "houtcomposiet",
    # Hout-engineered producten
    "lijmhout", "kruislaaghout", "i-balk", "i-balken", "lvl", "clt",
    # Zagerijen en houtbewerkingsbedrijven
    "zagerij", "zagerijen", "rondhoutzagerij",
    # Timmerbedrijven
    "timmerbedrijf", "timmerfabriek", "timmerwerkplaats",
    # Trappenindustrie
    "trappenindustrie", "trappenmaker", "trappenfabriek",
    "trappenbouw", "trappenmakerij",
    # Houtsoorten (uit CV)
    "naaldhout", "hardhout", "vuren", "grenen", "douglas",
    "douglashout", "vurenhout", "grenenhout", "eikenhout",
    "lariks", "eiken", "meranti", "azobé", "azobe", "iroko",
    "thermohout", "thermisch gemodificeerd",
    "verduurzaamd hout", "gecoat hout",
    "tropisch hout", "afrikaans hardhout",
    # Plaat / panelen
    "plaatmateriaal", "plaatmaterialen", "plywood", "multiplex",
    "osb", "mdf", "spaanplaat", "vezelplaat", "panelen",
    # Aanpalend
    "bouwmaterialen", "bouwmateriaal", "gevelbekleding",
    "kozijnen", "hsb",
    # 'deuren' / 'pallets' alleen specifiek (anders matcht het 'deuren openen'
    # of 'pallet unpacking' in logistics-contexten)
    "houten deuren", "binnendeuren", "buitendeuren", "voordeuren",
    "timmerwerk", "timmerindustrie", "schrijnwerkerij",
    "parket", "houten vloeren",
    # Bouwsector — directe afnemers van hout/bouwmateriaal
    "bouw", "bouwbranche", "bouwsector",
    "aannemer", "aannemerij", "bouwbedrijf",
    "bouwprojecten", "bouwlogistiek", "bouwmanagement",
    "woningbouw", "utiliteitsbouw", "infrabouw",
    "nieuwbouw", "renovatie", "verbouw",
    "prefab", "prefabricage", "prefabbouw",
    "infrastructuur", "infra ",
    # Bouwsubdisciplines (commercieel relevant)
    "betonbouw", "betonindustrie", "metaalbouw", "staalbouw",
    "dakdekker", "dakwerken", "dakwerkers",
    "steenfabriek", "steenindustrie",
    "beglazing", "glasindustrie",
    # Meubelindustrie / interieurbouw (hout-gebruikers)
    "meubelindustrie", "meubelmaker", "meubelfabrikant",
    "meubelproductie", "interieurbouw", "interieurmaker",
    # Verpakkingsindustrie hout (alleen specifiek, geen losse "pallet")
    "palletindustrie", "palletfabriek",
    "houten verpakking", "exportkrat", "houten kratten",
    # Tuinhout / buitenhout
    "tuinhout", "schutting", "tuinhuis", "vlonder",
    "terrasplank", "buitenhout",
    # Gevel- en daktechniek (hout/plaat-toepassingen)
    "gevelbouw", "geveltechniek", "gevelelement",
    "dakconstructie", "kapconstructie", "dakelement",
    # Isolatie (vaak via dezelfde grossier als hout/plaat)
    "isolatieplaat", "isolatiemateriaal",
    # Hout-halffabricaten / dimensies
    "balken", "planken", "latten", "rondhout", "schrooth",
]

# Bekende hout/bouwmateriaal-bedrijven NL (boost score als werkgever match)
HOUT_COMPANIES_NL = [
    # Klassieke houthandel NL
    "jongeneel", "pontmeyer", "stiho", "bouwmaat", "wilbrink",
    "boogaerdt", "fetim", "lemahieu", "carpentier",
    "centrop", "callens", "van de stadt", "jenowood",
    "gras houtimport", "noord-europese", "wijma", "kuiken",
    "haitsma", "rovas", "decospan", "norbord", "spano",
    "fibox", "raab karcher", "raab-karcher", "bouwcenter",
    "deli home", "deli xl", "beuk hout",
    "houthandel", "houtimport", "houtindustrie",
    "kappa houtindustrie", "moralt", "huberlu",
    "smit hout", "smithout", "smith hout",
    "koninklijke houthandel", "houtland", "verwol",
    # Plaat / panelen
    "kvh hout", "primaplaat", "mediahout",
    # Bouwmateriaal grossier (relevant voor Niels' segment)
    "raab karcher", "bmn", "bouwspecialist", "isobouw",
    "saint-gobain bouwmaterialen", "huberluxx",
    # Timmerindustrie (klanten)
    "berkvens", "skantrae", "weekamp", "bruynzeel deuren",
    # Tropisch hout / specialisten
    "boogaerdt", "tps hout", "houthandel van aalst",
    "timber and building supplies", "tbs holland",
]

# Vlaamse hout-bedrijven (België NL-talig)
HOUT_COMPANIES_BE = [
    "decospan", "lemahieu", "carpentier", "spano", "norbord",
    "fibox", "lecot", "bostoen", "spaensch hout", "pacquet",
    "devolder", "isoproc", "houtland", "houthandel vyncke",
    "pollet hout", "decoplus", "houthandel decock",
    "wijckmans hout", "deceuninck", "houthandel andries",
]

# Bouwmaterialen-grossiers / -handelaren NL (Niels' segment uit CV)
BOUWMATERIAAL_COMPANIES_NL = [
    # Grote ketens / grossiers
    "raab karcher", "raab-karcher", "saint-gobain",
    "stiho", "bouwmaat", "bmn", "bouwcenter",
    "pontmeyer", "jongeneel", "wilbrink",
    "deli home", "deli xl",
    "cb bouwmaterialen", "cb hout",
    "bouwspecialist", "isobouw",
    # Regionaal / familiebedrijf
    "heuts", "niemeijer bouwmaterialen", "duys bouwmaterialen",
    "linthorst", "klomps bouwmaterialen", "brouwers bouwmaterialen",
    "slaakboer", "bron bouwmaterialen", "holtkamp",
    "boumaat", "huberluxx", "huberlu",
    "galvano", "hmc bouw", "ibc bouw",
    "wolseley", "sanitiq", "hofa", "vbi",
    # Bouwmateriaal-fabrikanten waar commerciële rol zinnig is
    "wienerberger", "rockwool", "knauf", "saint-gobain weber",
    "gypsum nederland", "kingspan", "etex", "isover",
    "royal mosa", "mosa tegels",
    "fermacell", "rigips", "ytong", "siniat",
    # Bouwmateriaal-toeleveranciers (kozijnen / deuren / gevel)
    "berkvens", "skantrae", "weekamp", "bruynzeel deuren",
    "bruynzeel keukens", "metaglas", "schüco", "schueco",
    "reynaers", "alukon", "rehau",
    "rockpanel", "trespa", "eternit", "cembrit",
]

# Bouwmaterialen NL+BE Vlaanderen
BOUWMATERIAAL_COMPANIES_BE = [
    "lecot", "lambrecht bouwmaterialen", "loose bouw",
    "buggenhout bouwmaterialen", "facq", "desco",
    "imperial bouwmaterialen", "vlassenroot", "decotrans",
    "pieckaert", "plaspack", "devagro",
    "bostoen", "wienerberger benelux", "etex",
    "deceuninck", "reynaers belgium",
]

BOUWMATERIAAL_COMPANIES = BOUWMATERIAAL_COMPANIES_NL + BOUWMATERIAAL_COMPANIES_BE

HOUT_COMPANIES = HOUT_COMPANIES_NL + HOUT_COMPANIES_BE + BOUWMATERIAAL_COMPANIES

# Termen in titel die een hogere match-score verdienen (Niels' doelrollen)
HIGH_VALUE_TITLE_TERMS = [
    "manager", "business", "development", "sales",
    "bedrijfsleider", "vestigingsmanager",
]

# Soft uitsluit — alleen excluden als geen senior leadership-term in titel.
# 'Technisch Commercieel Manager' / 'Specialist Accountmanager' blijven dus door.
SOFT_NEGATIVE_TITLE_SUBSTRINGS = [
    "specialist", "technisch", "technical",
]
SENIOR_OK_PATTERN = (
    r"\b(manager|managing|directeur|director|bedrijfsleider|vestigingsmanager"
    r"|country|general|head of|chief|hoofd|leader|lead)\b"
)

# HARD UITSLUITEN — als deze substring in titel zit, score = 0.
# Substring-match (niet word-boundary), dus 'magazijn' matcht ook 'magazijnmedewerker'.
STRICT_NEGATIVE_TITLE_SUBSTRINGS = [
    "operator", "magazijn", "medewerker", "chauffeur", "vrachtwagen",
    "monteur", "timmerman", "schilder", "loodgieter", "metselaar",
    "stratenmaker", "schrijnwerker", "elektricien",
    "machinaal", "modelmaker", "tekenaar", "constructeur",
    "voorman", "ploegleider", "uitvoerder", "werkvoorbereider",
    "verpleegkundige", "verzorgende", "zorgkundige",
    "pedagogisch", "kinderopvang", "kinderdagverblijf",
    "kinderdagcentrum", "ziekenhuis", "verpleeghuis",
    "verzorgingstehuis", "thuiszorg",
    "uitzendbedrijf", "uitzendbureau",
    "leerling", "stagiair", "trainee", "bijbaan",
    "orderpicker", "expediteur", "machinist", "machinebediener",
    "horeca", "restaurant", "kapper", "kapsalon", "haarstylist",
    "kliniek", "oogkliniek", "tandarts",
    "uitgeverij", "uitgever", "boeken",
    "customer goods", "consumer goods",
    "speelgoed", "huishoudartikelen", "spellen",
    # IT / ERP / data / engineering (geen commerciële rol)
    "ict", "erp", "crm", "saas",
    "software", "frontend", "back-end", "backend", "fullstack",
    "developer ", " developer", "ontwikkelaar",
    "data analyst", "data engineer", "data scientist",
    "business analyst", "process analyst", "system analyst",
    "analyst", "analist",
    "devops", "sysadmin", "scrum", "qa engineer", "tester",
    "consultant",
    "view job opportunity",
    "productie",  # productieleider/productiemedewerker/teamlead productie
    # Retail / beauty / fashion (niet hout/bouw)
    "retail", "winkelketen", "winkelmanager",
    "beauty", "cosmetica", "parfumerie", "drogisterij",
    "fashion", "mode-", "modemerk", "kleding", "schoenen",
    "supermarkt", "buurtsuper",
    # Healthcare / pharma / zorg
    "healthcare", "gezondheidszorg", "zorgsector", "zorginstelling",
    "pharma", "farma", "farmaceutisch", "pharmaceutical",
    "medisch", "medical", "biotech",
    # Food / voeding / FMCG
    "food", "voeding", "voedingssector", "foodservice",
    "fmcg", "consumer goods",
    "drank", "beverage", "snack", "dairy", "zuivel",
    # Finance / verzekeringen
    "insurance", "verzekering", "verzekeraar", "verzekeringen",
    "finance ", "banking", "bankwezen", "bank ",
    # Automotive / IT / energie / onderwijs
    "automotive", "autohandel", "autobedrijf",
    "telecom", "software", " it ",
    "energiesector", "utilities",
    "onderwijs", "school", "universiteit", "hogeschool",
    # Werving / staffing (Niels' rol is bij eindwerkgever, niet bij detachering)
    "werving en selectie", "wervingsbureau", "detachering",
    # Te licht / niet senior commercieel
    "bediende", "balie", "baliebediende", "receptionist", "secretaresse",
    "packer", "packing", "verpakker",
    "assistent administr", "administratief",
    "flexjobber", "flexkracht", "uitzendkracht",
    "showroom",
    # Technisch / R&D / engineering (geen commerciële rol)
    "ingenieur", "engineer", "r&d", "research",
    "innovator", "innovatie ingenieur",
    "kwaliteits", "qhse", "lab ", "laborant",
    "modelleur", "modeleur",
    # Vakvaardigheid / uitvoerend in bouw
    "meubelmaker", "houtskeletbouwer",
    "bankwerker", "lasser", "plaatser",
    "logistiek",
]

# Recruitment-bureaus actief in bouw/hout/industrie (matcht naam in vacature)
RECRUITERS_BUILDING = [
    "bouwteam", "westerduin", "continu", "profmatch",
    "bvr recruitment", "bbr bouw", "bouwzaken", "buildung",
    "talent in de bouw", "bouwmensen", "nedbouw",
    "carriere.nu", "ipsa", "dejong recruitment bouw",
    "fortes recruitment", "ditisyourjob", "techfocus",
    "exsell", "executives only", "yacht",
    "bouwrecruiters", "huntfor", "wood recruitment",
]

# ──────────────────────────────────────────────────────────
# Zoekqueries — matrix van rol × industrie/product
# ──────────────────────────────────────────────────────────
QUERIES = [
    # Leadership × hout
    "vestigingsmanager hout",
    "vestigingsmanager houthandel",
    "bedrijfsleider hout",
    "bedrijfsleider houthandel",
    "commercieel manager hout",
    "commercieel manager houthandel",
    "commercieel manager houtimport",
    "commercieel directeur hout",
    "directeur houthandel",
    "operations manager hout",
    "general manager wood",
    "country manager wood",
    "country manager timber",
    # Sales / accountmanagement × hout
    "sales manager hout",
    "sales manager houthandel",
    "salesmanager houtimport",
    "senior accountmanager hout",
    "senior accountmanager houthandel",
    "key accountmanager hout",
    "nationaal accountmanager hout",
    "business development hout",
    "business development manager wood",
    "regio manager hout",
    "regiomanager houthandel",
    # Specialisaties (CV-producten)
    "accountmanager naaldhout",
    "accountmanager hardhout",
    "accountmanager plaatmateriaal",
    "manager douglashout",
    "commercieel manager bouwmaterialen",
    "salesmanager bouwmaterialen",
    "commercieel manager plaatmateriaal",
    "vestigingsmanager bouwmaterialen",
    "key accountmanager timmerindustrie",
    # Branche-aanpalend
    "manager houtindustrie",
    "manager houtbewerking",
    "manager houtskeletbouw",
    "directeur bouwmaterialen",
    # Engelstalig
    "sales manager wood netherlands",
    "business development manager timber",
    "key account manager wood",
]

# Brede queries voor branche-aggregators (Bouwjobs, Jobbird)
# Deze sites filteren minder strict op zoekwoord, dus we gebruiken brede
# branche-termen en laten scoring het uitsorteren.
BROAD_QUERIES = [
    # Hout algemeen
    "hout",
    "houthandel",
    "houtimport",
    "houtindustrie",
    "houthandelaar",
    "houtbewerking",
    # Hout-soorten (uit Niels' CV)
    "naaldhout",
    "hardhout",
    "douglashout",
    "vurenhout",
    "thermohout",
    "verduurzaamd hout",
    # Plaat / bouwmateriaal
    "plaatmateriaal",
    "bouwmaterialen",
    "gevelbekleding",
    # Hout-gerelateerde branches
    "houtskeletbouw",
    "timmerindustrie",
    "trappenindustrie",
    "zagerij",
    "meubelindustrie",
]

# ──────────────────────────────────────────────────────────
# Locaties — NL + Vlaanderen (België NL-talig)
# Niels woont Assendelft (Zaanstreek) maar reist
# ──────────────────────────────────────────────────────────
LOCATIONS_NL = ["Netherlands", "Nederland"]
LOCATIONS_BE_NL = ["Belgium", "Flanders", "Vlaanderen", "Antwerp", "Antwerpen"]

# Steden voor scoring-boost (dichter bij Assendelft = hoger)
CITIES_NEAR = [  # Zaanstreek + directe omgeving
    "assendelft", "zaandam", "zaanstad", "wormerveer",
    "amsterdam", "haarlem", "purmerend", "alkmaar",
    "hoofddorp", "amstelveen", "beverwijk", "ijmuiden",
    "heerhugowaard", "schiphol",
]
CITIES_RANDSTAD = [
    "utrecht", "rotterdam", "den haag", "leiden", "almere",
    "hilversum", "leidschendam", "delft", "gouda",
]
CITIES_BE_NL = [
    "antwerpen", "antwerp", "gent", "ghent", "brugge", "bruges",
    "leuven", "hasselt", "mechelen", "kortrijk", "rekkem",
    "aalst", "sint-niklaas", "turnhout", "genk",
    "vlaams-brabant", "oost-vlaanderen", "west-vlaanderen",
    "limburg", "antwerpen",
]

# ──────────────────────────────────────────────────────────
# Boost & negatief
# ──────────────────────────────────────────────────────────
POSITIVE_BOOST = [
    "opzetten", "opbouwen", "lanceren", "nieuwe markt", "greenfield",
    "scratch", "ondernemend", "leidinggevend", "team", "p&l",
    "marktontwikkeling", "uitbouwen", "groei",
]

NEGATIVE_TERMS = [
    # Niveau te laag / niet senior genoeg
    "junior", "medior", "stagiair", "stage ", " stage", "intern ",
    "trainee", "starter", "bijbaan", "parttime student",
    "studentenbaan", "zaterdaghulp",
    "leerling", "leer-werk", "leerwerk", "bbl", "bbl-traject",
    "duaal traject", "leerlingplek", "mbo-traject", "werkstudent",
    # Operationele / logistieke rollen (geen senior commerciële of management rol)
    "magazijnmedewerker", "magazijnhulp", "magazijnier",
    "chauffeur", "heftruckchauffeur", "vrachtwagenchauffeur",
    "kraanchauffeur", "kraanmachinist",
    "orderpicker", "expediteur", "expeditiemedewerker",
    "logistiek medewerker", "logistiekmedewerker",
    # Winkel- / baliepersoneel
    "baliemedewerker", "balieverkoper",
    "verkoopmedewerker", "winkelmedewerker",
    # Productie / montage / vakvaardig
    "productiemedewerker", "productiehulp",
    "montagemedewerker", "monteur", "servicemonteur",
    "operator", "machine-operator", "machinist", "machinebediener",
    "machinaal houtbewerker", "houtbewerker",
    "timmerman", "werkplaatstimmerman", "schrijnwerker",
    "elektricien", "schilder", "loodgieter",
    "bouwvakker", "metselaar", "stratenmaker",
    # Werkleiding / uitvoering (geen senior commerciële rol)
    "werkvoorbereider", "voorman", "ploegleider",
    "werkleider", "werkmeester", "uitvoerder",
    "aankomend bedrijfsleider", "lijnverantwoordelijke",
    # Technische / engineering / tekenkamer
    "tekenaar", "cad-tekenaar", "cad tekenaar",
    "constructeur", "calculator", "modelmaker",
    # Zorg / kinderopvang (geheel andere branche)
    "verpleegkundige", "verzorgende", "zorgkundige",
    "ziekenverzorgende", "zorgmedewerker", "thuiszorg",
    "pedagogisch", "kinderopvang", "babygroep",
]

# Locatie-negatief: niet-Nederlandstalig deel BE en buitenland behalve toegestane
NEGATIVE_LOCATIONS_BE = [
    "wallon", "wallonie", "wallonië", "liège", "luik",
    "namur", "namen", "charleroi", "mons", "bergen",
]

# ──────────────────────────────────────────────────────────
# HTTP / scraper instellingen
# ──────────────────────────────────────────────────────────
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

REQUEST_TIMEOUT = 20
REQUEST_DELAY_SECONDS = 0.8
MAX_RESULTS_PER_QUERY = 50
DAYS_BACK = 30
