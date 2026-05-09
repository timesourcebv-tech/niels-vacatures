"""Streamlit-dashboard voor Niels.

Lokaal:        streamlit run dashboard.py
Online:        Streamlit Community Cloud — entrypoint = dashboard.py
"""
from __future__ import annotations

import datetime as _dt
import hashlib as _hashlib
import html as _html
import re as _re

import extra_streamlit_components as stx
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup

from config import HOUT_COMPANIES, INDUSTRY_KEYWORDS, NIELS_PROFILE
from db import fetch_jobs, get_conn, stats, toggle_favorite, update_status


def _industry_match(row: pd.Series) -> bool:
    """True als titel, bedrijf óf beschrijving een hout/bouw-signaal bevat."""
    title = str(row.get("title") or "").lower()
    company = str(row.get("company") or "").lower()
    desc = str(row.get("description") or "").lower()[:1500]
    blob = f" {title} {company} {desc} "
    for kw in INDUSTRY_KEYWORDS:
        if _re.search(r"\b" + _re.escape(kw) + r"\b", blob):
            return True
    for c in HOUT_COMPANIES:
        if _re.search(r"\b" + _re.escape(c) + r"\b", company):
            return True
    return False


def _clean_description(raw: object) -> str:
    """Strip HTML-tags en decodeer entities — Adzuna levert description met HTML."""
    if not raw:
        return ""
    s = str(raw)
    if "<" in s and ">" in s:
        s = BeautifulSoup(s, "lxml").get_text(" ", strip=True)
    s = _html.unescape(s)
    s = _re.sub(r"\s+", " ", s).strip()
    return s

# Per provincie: trefwoorden die in de location-string kunnen voorkomen
# (provincienaam + grote en kleine steden in die provincie).
PROVINCIES: dict[str, list[str]] = {
    "🇳🇱 Noord-Holland": [
        "noord-holland", "noord holland",
        "amsterdam", "haarlem", "alkmaar", "zaandam", "zaanstad", "zaanstreek",
        "purmerend", "hoorn", "amstelveen", "hoofddorp", "haarlemmermeer",
        "wormerveer", "heerhugowaard", "beverwijk", "ijmuiden", "assendelft",
        "schiphol", "den helder", "hilversum", "weesp", "diemen", "edam",
        "uitgeest", "castricum", "bergen", "heemstede", "zandvoort", "naarden",
    ],
    "🇳🇱 Zuid-Holland": [
        "zuid-holland", "zuid holland",
        "rotterdam", "den haag", "the hague", "leiden", "delft", "dordrecht",
        "gouda", "schiedam", "vlaardingen", "spijkenisse", "zoetermeer",
        "leidschendam", "voorburg", "rijswijk", "alphen aan den rijn",
        "capelle aan den ijssel", "ridderkerk", "barendrecht", "papendrecht",
    ],
    "🇳🇱 Utrecht": [
        "provincie utrecht", "utrecht,", "utrecht ", "utrecht-",
        "amersfoort", "nieuwegein", "houten", "veenendaal", "zeist",
        "ijsselstein", "woerden", "de meern", "leusden",
    ],
    "🇳🇱 Gelderland": [
        "gelderland",
        "arnhem", "nijmegen", "apeldoorn", "ede", "tiel", "harderwijk",
        "doetinchem", "zutphen", "wageningen", "winterswijk",
    ],
    "🇳🇱 Noord-Brabant": [
        "noord-brabant", "brabant",
        "eindhoven", "tilburg", "breda", "den bosch", "'s-hertogenbosch",
        "helmond", "oss", "roosendaal", "bergen op zoom", "veldhoven",
        "oosterhout", "etten-leur", "waalwijk", "uden",
    ],
    "🇳🇱 Overijssel": [
        "overijssel",
        "zwolle", "enschede", "deventer", "hengelo", "almelo", "kampen",
    ],
    "🇳🇱 Limburg (NL)": [
        "limburg, nederland", "limburg,nl",
        "maastricht", "venlo", "heerlen", "sittard", "roermond", "weert",
        "kerkrade",
    ],
    "🇳🇱 Flevoland": [
        "flevoland",
        "almere", "lelystad", "dronten", "emmeloord",
    ],
    "🇳🇱 Friesland": [
        "friesland", "fryslân", "fryslan",
        "leeuwarden", "drachten", "sneek", "heerenveen",
    ],
    "🇳🇱 Groningen": [
        "groningen, nederland", "provincie groningen",
        "groningen,", "delfzijl", "hoogezand",
    ],
    "🇳🇱 Drenthe": [
        "drenthe",
        "assen", "emmen", "meppel", "hoogeveen",
    ],
    "🇳🇱 Zeeland": [
        "zeeland",
        "middelburg", "vlissingen", "goes", "terneuzen",
    ],
    "🇧🇪 Antwerpen": [
        "antwerpen", "antwerp",
        "mechelen", "turnhout", "lier", "geel", "mortsel", "edegem",
        "schoten", "kontich", "boom", "willebroek", "heist-op-den-berg",
    ],
    "🇧🇪 Oost-Vlaanderen": [
        "oost-vlaanderen",
        "gent", "ghent", "aalst", "sint-niklaas", "dendermonde",
        "ronse", "ninove", "deinze", "eeklo", "wetteren",
    ],
    "🇧🇪 West-Vlaanderen": [
        "west-vlaanderen",
        "brugge", "bruges", "kortrijk", "oostende", "roeselare",
        "ieper", "wielsbeke", "menen", "rekkem", "tielt", "torhout",
        "knokke", "diksmuide",
    ],
    "🇧🇪 Vlaams-Brabant": [
        "vlaams-brabant",
        "leuven", "tienen", "halle", "vilvoorde", "aarschot", "diest",
        "asse", "tervuren", "zaventem",
    ],
    "🇧🇪 Limburg (BE)": [
        "limburg, belg", "limburg, vlaa",
        "hasselt", "genk", "tongeren", "sint-truiden", "lommel",
        "beringen", "bilzen", "maasmechelen",
    ],
}

st.set_page_config(
    page_title="Vacaturemonitor — Hout & Bouwmaterialen",
    page_icon="🪵",
    layout="wide",
)

# Theme toggle — voor CSS-injectie zodat de juiste palette wordt geladen
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False
DARK = st.session_state["dark_mode"]

# ── Nexus-stijl CSS (light + dark) ────────────────────────────────────
# Geen font-family override — Streamlit's Source Sans 3 + Material Symbols
# blijven intact, anders breken pijltjes/hartjes als icoon-glyphs.
NEXUS_CSS = """
<style>
/* === Light (default) === */
[data-testid="stAppViewContainer"], [data-testid="stMain"], section.main,
.stApp { background: #f5f5f7 !important; }
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid rgba(0,0,0,0.08) !important;
}

.nv-header {
    background: #ffffff;
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 12px;
    padding: 1.6rem 1.8rem 1.4rem 1.8rem;
    margin: 0 0 1.2rem 0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.nv-header h1 {
    color: #1d1d1f;
    font-size: 1.7rem;
    font-weight: 700;
    margin: 0 0 0.35rem 0;
    letter-spacing: -0.02em;
    line-height: 1.2;
}
.nv-header .nv-subtitle {
    color: #86868b;
    font-size: 0.96rem;
    margin: 0;
    line-height: 1.45;
}

[data-testid="stContainer"] > [data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff !important;
    border: 1px solid rgba(0,0,0,0.08) !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    transition: box-shadow 0.18s ease, border-color 0.18s ease;
}
[data-testid="stContainer"] > [data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 3px 12px rgba(0,0,0,0.08);
    border-color: rgba(0,0,0,0.14) !important;
}

[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid rgba(0,0,0,0.08);
    padding: 0.9rem 1.1rem;
    border-radius: 10px;
}
[data-testid="stMetricValue"] {
    font-weight: 700;
    color: #1d1d1f;
    font-size: 1.5rem;
    letter-spacing: -0.02em;
}
[data-testid="stMetricLabel"] {
    font-size: 0.78rem;
    color: #86868b;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.nv-score {
    display: inline-block;
    padding: 0.32rem 0.8rem;
    border-radius: 980px;
    font-weight: 600;
    font-size: 0.84rem;
    white-space: nowrap;
    letter-spacing: -0.01em;
}
.nv-score-high { background: rgba(0,113,227,0.10); color: #0071e3; }
.nv-score-mid  { background: rgba(232,85,26,0.10); color: #E8551A; }
.nv-score-low  { background: #f5f5f7; color: #86868b; }

.nv-job-title {
    font-size: 1.18rem;
    font-weight: 700;
    color: #1d1d1f;
    margin: 0 0 0.25rem 0;
    line-height: 1.32;
    letter-spacing: -0.015em;
}
.nv-job-title a { color: #1d1d1f; text-decoration: none; }
.nv-job-title a:hover { color: #0071e3; }
.nv-job-meta {
    color: #424245;
    font-size: 0.94rem;
    margin: 0 0 0.55rem 0;
    line-height: 1.45;
}
.nv-job-meta strong { color: #1d1d1f; font-weight: 600; }
.nv-job-meta .nv-source {
    color: #86868b;
    font-size: 0.78rem;
    margin-left: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.nv-job-summary {
    color: #424245;
    font-size: 0.92rem;
    line-height: 1.6;
    margin: 0.35rem 0 0.45rem 0;
}

[data-testid="stSidebar"] h2 {
    color: #1d1d1f;
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem;
}
[data-testid="stSidebar"] label {
    color: #1d1d1f;
    font-weight: 500;
    font-size: 0.9rem;
}

[data-baseweb="tag"] {
    background-color: #f5f5f7 !important;
    color: #1d1d1f !important;
    border-radius: 6px !important;
    border: 1px solid rgba(0,0,0,0.08) !important;
    font-weight: 500 !important;
}
[data-baseweb="tag"] svg {
    color: #86868b !important;
    fill: #86868b !important;
}

[data-baseweb="select"] > div,
.stTextInput input,
.stTextArea textarea {
    background: #ffffff !important;
    border-radius: 8px !important;
    border-color: rgba(0,0,0,0.14) !important;
}

.stButton button {
    background: #ffffff;
    border: 1px solid rgba(0,0,0,0.14);
    color: #1d1d1f;
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.15s ease;
}
.stButton button:hover {
    background: #fafafa;
    border-color: rgba(0,0,0,0.22);
}
.stFormSubmitButton button {
    background: #0071e3;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-weight: 600;
}
.stFormSubmitButton button:hover { background: #0077ed; }

.nv-metric-tile button {
    background: #ffffff !important;
    border: 1px solid rgba(0,0,0,0.08) !important;
    border-radius: 10px !important;
    padding: 0.95rem 1.1rem !important;
    height: auto !important;
    min-height: 5.2rem !important;
    text-align: left !important;
    white-space: pre-line !important;
    font-weight: 600 !important;
    line-height: 1.35 !important;
    color: #1d1d1f !important;
    transition: all 0.15s ease;
}
.nv-metric-tile button:hover { border-color: rgba(0,0,0,0.18) !important; }
.nv-metric-tile-active button {
    background: rgba(0,113,227,0.08) !important;
    border-color: #0071e3 !important;
    color: #0071e3 !important;
}
.nv-metric-tile button p {
    font-size: 0.74rem !important;
    color: #86868b !important;
    margin: 0 0 0.3rem 0 !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}
.nv-metric-tile-active button p { color: #0071e3 !important; }

.nv-fav-btn button {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    font-size: 1.4rem !important;
    line-height: 1 !important;
    cursor: pointer;
    box-shadow: none !important;
    min-height: 0 !important;
    transition: transform 0.1s ease;
}
.nv-fav-btn button:hover { transform: scale(1.15); background: transparent !important; }
.nv-fav-btn button:focus { outline: none !important; box-shadow: none !important; }

.stCaption, [data-testid="stCaptionContainer"] {
    color: #86868b;
    font-size: 0.84rem;
}

h1, h2, h3, h4 {
    color: #1d1d1f;
    letter-spacing: -0.015em;
    font-weight: 700;
}
</style>
"""

NEXUS_DARK_CSS = """
<style>
/* === Dark overrides === */
[data-testid="stAppViewContainer"], [data-testid="stMain"], section.main,
.stApp { background: #000000 !important; }
[data-testid="stSidebar"] {
    background: #1c1c1e !important;
    border-right: 1px solid rgba(255,255,255,0.10) !important;
}

h1, h2, h3, h4, p, span, div, label, li { color: #f5f5f7; }

.nv-header {
    background: #1c1c1e;
    border-color: rgba(255,255,255,0.10);
    box-shadow: none;
}
.nv-header h1 { color: #f5f5f7; }
.nv-header .nv-subtitle { color: #8e8e93; }

[data-testid="stContainer"] > [data-testid="stVerticalBlockBorderWrapper"] {
    background: #1c1c1e !important;
    border-color: rgba(255,255,255,0.10) !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.35) !important;
}
[data-testid="stContainer"] > [data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.5) !important;
    border-color: rgba(255,255,255,0.18) !important;
}

[data-testid="stMetric"] {
    background: #1c1c1e;
    border-color: rgba(255,255,255,0.10);
}
[data-testid="stMetricValue"] { color: #f5f5f7; }
[data-testid="stMetricLabel"] { color: #8e8e93; }

.nv-score-high { background: rgba(0,113,227,0.18) !important; color: #4DA3FF !important; }
.nv-score-mid  { background: rgba(232,85,26,0.18) !important; color: #FF9966 !important; }
.nv-score-low  { background: #2c2c2e !important; color: #8e8e93 !important; }

.nv-job-title, .nv-job-title a { color: #f5f5f7 !important; }
.nv-job-title a:hover { color: #4DA3FF !important; }
.nv-job-meta { color: #d1d1d6 !important; }
.nv-job-meta strong { color: #f5f5f7 !important; }
.nv-job-meta .nv-source { color: #8e8e93 !important; }
.nv-job-summary { color: #d1d1d6 !important; }

[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] label,
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
    color: #f5f5f7 !important;
}

[data-baseweb="tag"] {
    background-color: #2c2c2e !important;
    color: #f5f5f7 !important;
    border-color: rgba(255,255,255,0.10) !important;
}
[data-baseweb="tag"] svg { color: #8e8e93 !important; fill: #8e8e93 !important; }

[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea,
[data-baseweb="popover"], [data-baseweb="menu"] {
    background: #2c2c2e !important;
    color: #f5f5f7 !important;
    border-color: rgba(255,255,255,0.10) !important;
}

.stButton button {
    background: #1c1c1e !important;
    border-color: rgba(255,255,255,0.10) !important;
    color: #f5f5f7 !important;
}
.stButton button:hover {
    background: #2c2c2e !important;
    border-color: rgba(255,255,255,0.18) !important;
}

.nv-metric-tile button {
    background: #1c1c1e !important;
    border-color: rgba(255,255,255,0.10) !important;
    color: #f5f5f7 !important;
}
.nv-metric-tile button:hover { border-color: rgba(255,255,255,0.18) !important; }
.nv-metric-tile-active button {
    background: rgba(0,113,227,0.18) !important;
    border-color: #0071e3 !important;
    color: #4DA3FF !important;
}
.nv-metric-tile button p { color: #8e8e93 !important; }
.nv-metric-tile-active button p { color: #4DA3FF !important; }

.stCaption, [data-testid="stCaptionContainer"] { color: #8e8e93 !important; }
hr { border-color: rgba(255,255,255,0.10) !important; }
</style>
"""

st.markdown(NEXUS_CSS, unsafe_allow_html=True)
if DARK:
    st.markdown(NEXUS_DARK_CSS, unsafe_allow_html=True)

STATUS_LABELS = {
    "new": "Nieuw",
    "applied": "Gesolliciteerd",
    "rejected": "Afgewezen",
}
STATUS_OPTIONS = list(STATUS_LABELS.keys())


# ──────────────────────────────────────────────────────────
# Login-gate via Streamlit secrets (username + wachtwoord)
# Username wordt onthouden in een cookie (90 dagen).
# ──────────────────────────────────────────────────────────
def _auth_token(user: str, pw: str) -> str:
    """Tokenize de credentials zodat de session-cookie ongeldig wordt
    zodra het wachtwoord wijzigt."""
    return _hashlib.sha256(f"{user}:{pw}:nv-session-v1".encode()).hexdigest()


def login_gate() -> bool:
    try:
        user_required = st.secrets.get("APP_USERNAME", "")
        pw_required = st.secrets.get("APP_PASSWORD", "")
    except Exception:
        user_required = pw_required = ""
    if not pw_required:
        return True
    if st.session_state.get("authed"):
        return True

    cookies = stx.CookieManager(key="niels_vac_cookies")

    # Auto-login via persistent session-cookie (max 30 dagen)
    expected_token = _auth_token(user_required, pw_required)
    saved_token = cookies.get("niels_session")
    if saved_token and saved_token == expected_token:
        st.session_state["authed"] = True
        return True

    saved_user = cookies.get("niels_username") or ""

    st.markdown(
        """
        <div class="nv-header">
            <h1>Vacaturemonitor</h1>
            <p class="nv-subtitle">Hout & bouwmaterialen — senior commercieel</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("login"):
        user = st.text_input("Gebruikersnaam", value=saved_user)
        pw = st.text_input("Wachtwoord", type="password")
        remember = st.checkbox("30 dagen ingelogd blijven", value=True)
        submitted = st.form_submit_button("Inloggen")
    if submitted:
        if user.strip().lower() == user_required.strip().lower() and pw == pw_required:
            cookies.set(
                "niels_username", user,
                expires_at=_dt.datetime.now() + _dt.timedelta(days=90),
                key="set_username",
            )
            if remember:
                cookies.set(
                    "niels_session", expected_token,
                    expires_at=_dt.datetime.now() + _dt.timedelta(days=30),
                    key="set_session",
                )
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Onjuiste gebruikersnaam of wachtwoord.")
    return False


def logout() -> None:
    """Verwijder session-cookie en sessie-state."""
    try:
        cookies = stx.CookieManager(key="niels_vac_cookies")
        cookies.delete("niels_session", key="del_session")
    except Exception:
        pass
    st.session_state["authed"] = False
    st.rerun()


def load_df(min_score: int, statuses: list[str]) -> pd.DataFrame:
    rows = fetch_jobs(min_score=min_score, statuses=statuses, limit=1000)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame([dict(r) for r in rows])
    # NaN → None zodat truthy-checks (`or`) en string-slicing werken zoals verwacht
    return df.astype(object).where(pd.notna(df), None)


def header() -> None:
    st.markdown(
        f"""
        <div class="nv-header">
            <h1>Vacaturemonitor</h1>
            <p class="nv-subtitle">
                Hout &amp; bouwmaterialen · Senior commercieel ·
                {NIELS_PROFILE['experience_years']}+ jaar ervaring ·
                {NIELS_PROFILE['career_history'][-1]}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    s = stats()
    if "active_view" not in st.session_state:
        st.session_state["active_view"] = "all"
    active = st.session_state["active_view"]

    tiles = [
        ("all", "Totaal", s.get("total") or 0),
        ("new", "Te bekijken", s.get("new_count") or 0),
        ("fav", "Favorieten", s.get("favorite_count") or 0),
        ("applied", "Gesolliciteerd", s.get("applied_count") or 0),
        ("rejected", "Afgewezen", s.get("rejected_count") or 0),
    ]
    cols = st.columns(5)
    for col, (key, label, value) in zip(cols, tiles):
        with col:
            active_cls = "nv-metric-tile-active" if active == key else ""
            st.markdown(f'<div class="nv-metric-tile {active_cls}">', unsafe_allow_html=True)
            if st.button(
                f"{label}\n{value}",
                key=f"tile_{key}",
                use_container_width=True,
            ):
                st.session_state["active_view"] = key
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    last_run = (s.get("last_run") or "—")[:16].replace("T", " ")
    st.caption(f"Laatst bijgewerkt: {last_run}")


def sidebar_filters() -> tuple[int, list[str], str, list[str], list[str], bool, bool]:
    with st.sidebar:
        # Theme-toggle bovenaan
        new_dark = st.toggle(
            "Donker thema",
            value=st.session_state.get("dark_mode", False),
            key="dark_toggle",
        )
        if new_dark != st.session_state.get("dark_mode", False):
            st.session_state["dark_mode"] = new_dark
            st.rerun()
        st.divider()
        st.header("Filters")
        # Kernvakgebied wordt al bij scrape afgedwongen — geen toggle meer nodig.
        vakgebied_only = False

        # Status & favorieten worden via de tegels bovenaan bestuurd.
        active = st.session_state.get("active_view", "all")
        if active == "all":
            statuses, favorites_only = STATUS_OPTIONS, False
        elif active == "new":
            statuses, favorites_only = ["new"], False
        elif active == "fav":
            statuses, favorites_only = STATUS_OPTIONS, True
        elif active == "applied":
            statuses, favorites_only = ["applied"], False
        elif active == "rejected":
            statuses, favorites_only = ["rejected"], False
        else:
            statuses, favorites_only = STATUS_OPTIONS, False

        min_score = 0

        # Provincies — checkbox-grid in expander
        with st.expander(
            f"Provincies",
            expanded=False,
        ):
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("Alles", key="prov_all", use_container_width=True):
                    for p in PROVINCIES:
                        st.session_state[f"prov_{p}"] = True
                    st.rerun()
            with cc2:
                if st.button("Geen", key="prov_none", use_container_width=True):
                    for p in PROVINCIES:
                        st.session_state[f"prov_{p}"] = False
                    st.rerun()
            provincies = []
            for prov in PROVINCIES:
                if st.checkbox(
                    prov,
                    value=st.session_state.get(f"prov_{prov}", True),
                    key=f"prov_{prov}",
                ):
                    provincies.append(prov)

        # Bronnen — checkbox-grid in expander
        with get_conn() as conn:
            sources_rows = conn.execute("SELECT DISTINCT source FROM jobs").fetchall()
        sources_all = sorted([r["source"] for r in sources_rows])
        with st.expander("Bronnen", expanded=False):
            sources = []
            for src in sources_all:
                if st.checkbox(
                    src,
                    value=st.session_state.get(f"src_{src}", True),
                    key=f"src_{src}",
                ):
                    sources.append(src)

        search = st.text_input("Zoeken in titel/bedrijf", "")

        st.divider()
        with st.expander("Niels' profiel"):
            for line in NIELS_PROFILE["specialties"]:
                st.markdown(f"- {line}")
            st.markdown("**Talen**: " + ", ".join(NIELS_PROFILE["languages"]))
            st.markdown("**Locatie**: " + NIELS_PROFILE["location"])

        if st.button("Uitloggen", key="logout_btn", use_container_width=True):
            logout()

        st.divider()
        st.caption(
            "Het scraper-script `run.py` wordt dagelijks via GitHub Actions "
            "uitgevoerd. Druk niet handmatig op refresh — kom morgen weer kijken "
            "voor nieuwe vacatures."
        )
    return min_score, statuses, search, sources, provincies, favorites_only, vakgebied_only


def render_job_card(row: pd.Series) -> None:
    raw_status = row["status"]
    status = raw_status if raw_status in STATUS_OPTIONS else "new"
    score = int(row["score"])
    title = row["title"]
    company = row["company"] or "Onbekend"
    location = row["location"] or "—"
    posted = str(row.get("posted_at") or row.get("discovered_at") or "")[:10]
    source = row["source"]
    is_fav = bool(row.get("favorite"))

    score_class = (
        "nv-score-high" if score >= 70
        else "nv-score-mid" if score >= 50
        else "nv-score-low"
    )
    fav_icon = "❤️" if is_fav else "🤍"
    fav_help = "Verwijder uit favorieten" if is_fav else "Markeer als favoriet"

    with st.container(border=True):
        c1, c2 = st.columns([5, 1.6])
        with c1:
            fav_col, title_col = st.columns([0.07, 0.93])
            with fav_col:
                st.markdown('<div class="nv-fav-btn">', unsafe_allow_html=True)
                if st.button(fav_icon, key=f"fav_{row['id']}", help=fav_help):
                    toggle_favorite(int(row["id"]))
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with title_col:
                st.markdown(
                    f"""
                    <div class="nv-job-title"><a href="{row['url']}" target="_blank">{title}</a></div>
                    <div class="nv-job-meta">
                        <strong>{company}</strong> · {location}
                        <span class="nv-source">{source} · {posted}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            desc = _clean_description(row.get("description"))
            if desc:
                short = desc if len(desc) <= 320 else desc[:317].rsplit(" ", 1)[0] + "…"
                st.markdown(
                    f"<div class='nv-job-summary'>{short}</div>",
                    unsafe_allow_html=True,
                )
                if len(desc) > 320:
                    with st.expander("Volledige beschrijving"):
                        st.write(desc)
        with c2:
            st.markdown(
                f"<div style='text-align:right;margin-bottom:0.5rem;'>"
                f"<span class='nv-score {score_class}'>{score} / 100</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            new_status = st.selectbox(
                "Status",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(status),
                format_func=lambda s: STATUS_LABELS[s],
                key=f"status_{row['id']}",
                label_visibility="collapsed",
            )
            if new_status != status:
                update_status(int(row["id"]), new_status, None)
                st.rerun()


def main() -> None:
    if not login_gate():
        return

    header()
    min_score, statuses, search, sources, provincies, favorites_only, vakgebied_only = sidebar_filters()

    if not statuses:
        st.info("Selecteer minstens één status in de sidebar.")
        return

    df = load_df(min_score=min_score, statuses=statuses)
    if df.empty:
        st.warning(
            "Geen vacatures gevonden voor deze filters. "
            "Run `python run.py` lokaal om vacatures op te halen."
        )
        return

    if favorites_only:
        df = df[df["favorite"].fillna(0).astype(int) == 1]
    if vakgebied_only and not df.empty:
        df = df[df.apply(_industry_match, axis=1)]
    if sources:
        df = df[df["source"].isin(sources)]
    if provincies and len(provincies) < len(PROVINCIES):
        loc_lower = df["location"].fillna("").str.lower()
        mask = pd.Series(False, index=df.index)
        for prov in provincies:
            for term in PROVINCIES[prov]:
                mask = mask | loc_lower.str.contains(term, na=False, regex=False)
        df = df[mask]
    if search:
        s = search.lower()
        mask = (
            df["title"].str.lower().str.contains(s, na=False)
            | df["company"].fillna("").str.lower().str.contains(s, na=False)
        )
        df = df[mask]

    if df.empty:
        st.info("Geen vacatures matchen jouw filters.")
        return

    sort_by = st.radio(
        "Sorteer op",
        ["Match-score", "Datum gevonden"],
        horizontal=True,
        index=0,
        label_visibility="collapsed",
    )
    if sort_by == "Datum gevonden":
        df = df.sort_values("discovered_at", ascending=False)
    else:
        df = df.sort_values(["score", "discovered_at"], ascending=[False, False])

    st.subheader(f"{len(df)} vacature(s)")
    st.caption("Gesorteerd op match-score, hoogste eerst.")

    for _, row in df.iterrows():
        render_job_card(row)


if __name__ == "__main__":
    main()
