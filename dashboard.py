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

from config import NIELS_PROFILE
from db import fetch_jobs, get_conn, stats, toggle_favorite, update_status


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

# Theme toggle — moet vóór CSS-injectie zodat de juiste tinten worden geladen
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False
DARK = st.session_state["dark_mode"]

# Kleurpalet — wisselt tussen licht en donker
if DARK:
    C = {
        "bg": "#1C1C1E", "bg_alt": "#2C2C2E", "card": "#2C2C2E",
        "border": "#38383A", "text": "#F5F5F7", "text_2": "#98989D",
        "text_3": "#636366", "tag_bg": "#3A3A3C", "tag_text": "#F5F5F7",
        "tag_close": "#98989D", "input_bg": "#2C2C2E",
        "score_high_bg": "#1B3A1F", "score_high_fg": "#A4D4A8",
        "score_mid_bg":  "#3D2E0F", "score_mid_fg":  "#F0C97A",
        "score_low_bg":  "#2C2C2E", "score_low_fg":  "#98989D",
    }
else:
    C = {
        "bg": "#FFFFFF", "bg_alt": "#F5F5F7", "card": "#FFFFFF",
        "border": "#E5E5E7", "text": "#1D1D1F", "text_2": "#424245",
        "text_3": "#86868B", "tag_bg": "#E8E8ED", "tag_text": "#1D1D1F",
        "tag_close": "#6E6E73", "input_bg": "#FFFFFF",
        "score_high_bg": "#E8F5E9", "score_high_fg": "#1B5E20",
        "score_mid_bg":  "#FFF3E0", "score_mid_fg":  "#B26A00",
        "score_low_bg":  "#F2F2F7", "score_low_fg":  "#6E6E73",
    }

# Apple-geïnspireerde styling — clean, leesbaar, ruimtelijk
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Globale typografie — Inter (universeel goed leesbaar) */
    html, body, [class*="css"], .stApp, [data-testid="stSidebar"],
    .stMarkdown, .stMarkdown p, .stMarkdown div, button, input, select, textarea {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    body, .stApp {
        font-size: 16px;
    }
    h1, h2, h3, h4 {
        font-family: 'Inter', -apple-system, sans-serif !important;
        letter-spacing: -0.01em;
        color: #1D1D1F;
        font-weight: 600;
    }
    .stApp {
        background: #FFFFFF;
    }

    /* Header */
    .nv-header {
        padding: 2rem 0 1rem 0;
        margin: 0 0 1.5rem 0;
        border-bottom: 1px solid #E5E5E7;
    }
    .nv-header h1 {
        font-size: 2.1rem;
        font-weight: 700;
        letter-spacing: -0.015em;
        color: #1D1D1F;
        margin: 0 0 0.4rem 0;
        line-height: 1.2;
    }
    .nv-header .nv-subtitle {
        color: #6E6E73;
        font-size: 1.05rem;
        font-weight: 400;
        margin: 0;
        line-height: 1.4;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background: #F5F5F7;
        padding: 1rem 1.2rem;
        border-radius: 12px;
    }
    [data-testid="stMetricValue"] {
        font-weight: 600;
        color: #1D1D1F;
        font-size: 1.6rem;
        letter-spacing: -0.02em;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        color: #6E6E73;
        font-weight: 500;
    }

    /* Vacature-cards */
    [data-testid="stContainer"] > [data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF !important;
        border: 1px solid #E5E5E7 !important;
        border-radius: 14px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    [data-testid="stContainer"] > [data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    }

    /* Score badge */
    .nv-score {
        display: inline-block;
        padding: 0.35rem 0.95rem;
        border-radius: 980px;
        font-weight: 600;
        font-size: 0.9rem;
        white-space: nowrap;
    }
    .nv-score-high { background: #E8F5E9; color: #1B5E20; }
    .nv-score-mid  { background: #FFF3E0; color: #B26A00; }
    .nv-score-low  { background: #F2F2F7; color: #6E6E73; }

    /* Vacature-titel */
    .nv-job-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1D1D1F;
        margin: 0 0 0.3rem 0;
        line-height: 1.35;
    }
    .nv-job-title a {
        color: #1D1D1F;
        text-decoration: none;
    }
    .nv-job-title a:hover {
        color: #0071E3;
    }
    .nv-job-meta {
        color: #424245;
        font-size: 0.98rem;
        margin: 0 0 0.6rem 0;
        line-height: 1.45;
    }
    .nv-job-meta strong {
        color: #1D1D1F;
        font-weight: 600;
    }
    .nv-job-meta .nv-source {
        color: #86868B;
        font-size: 0.85rem;
        margin-left: 0.5rem;
    }
    .nv-job-summary {
        color: #3A3A3C;
        font-size: 0.97rem;
        line-height: 1.6;
        margin: 0.4rem 0 0.5rem 0;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #F5F5F7;
        border-right: 1px solid #E5E5E7;
    }
    [data-testid="stSidebar"] h2 {
        color: #1D1D1F;
        font-size: 1.15rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        border-bottom: none;
        padding: 0;
        margin-bottom: 0.5rem;
    }
    [data-testid="stSidebar"] label {
        color: #1D1D1F;
        font-weight: 500;
        font-size: 0.95rem;
    }

    /* Multiselect tags / pillen — neutraal Apple-grijs i.p.v. donker bruin */
    [data-baseweb="tag"] {
        background-color: #E8E8ED !important;
        color: #1D1D1F !important;
        border-radius: 6px !important;
        border: none !important;
        font-weight: 500 !important;
    }
    [data-baseweb="tag"] svg {
        color: #6E6E73 !important;
        fill: #6E6E73 !important;
    }
    [data-baseweb="tag"]:hover {
        background-color: #DCDCE0 !important;
    }

    /* Inputs / dropdowns */
    [data-baseweb="select"] > div,
    .stTextInput input,
    .stTextArea textarea {
        background: #FFFFFF !important;
        border-radius: 8px !important;
        border-color: #D2D2D7 !important;
    }

    /* Buttons */
    .stButton button {
        background: #FFFFFF;
        border: 1px solid #D2D2D7;
        color: #1D1D1F;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.15s ease;
    }
    .stButton button:hover {
        background: #F5F5F7;
        border-color: #B0B0B5;
    }
    .stButton button[kind="primary"], .stFormSubmitButton button {
        background: #0071E3;
        color: #FFFFFF;
        border: none;
    }
    .stButton button[kind="primary"]:hover, .stFormSubmitButton button:hover {
        background: #0077ED;
    }

    /* Captions kleiner en grijzer */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #86868B;
        font-size: 0.88rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Donker thema — overrides bovenop het standaard lichte thema
if DARK:
    st.markdown(
        """
        <style>
        .stApp, body { background: #1C1C1E !important; color: #F5F5F7 !important; }
        h1, h2, h3, h4 { color: #F5F5F7 !important; }
        p, span, div, label, li { color: #E5E5E7; }
        .nv-header { border-bottom-color: #38383A !important; }
        .nv-header h1 { color: #F5F5F7 !important; }
        .nv-header .nv-subtitle { color: #98989D !important; }
        [data-testid="stMetric"] { background: #2C2C2E !important; }
        [data-testid="stMetricValue"] { color: #F5F5F7 !important; }
        [data-testid="stMetricLabel"] { color: #98989D !important; }
        [data-testid="stContainer"] > [data-testid="stVerticalBlockBorderWrapper"] {
            background: #2C2C2E !important;
            border-color: #38383A !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2) !important;
        }
        [data-testid="stContainer"] > [data-testid="stVerticalBlockBorderWrapper"]:hover {
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4) !important;
        }
        .nv-job-title, .nv-job-title a { color: #F5F5F7 !important; }
        .nv-job-title a:hover { color: #4DA3FF !important; }
        .nv-job-meta { color: #C7C7CC !important; }
        .nv-job-meta strong { color: #F5F5F7 !important; }
        .nv-job-meta .nv-source { color: #98989D !important; }
        .nv-job-summary { color: #C7C7CC !important; }
        .nv-score-high { background: #1B3A1F !important; color: #A4D4A8 !important; }
        .nv-score-mid  { background: #3D2E0F !important; color: #F0C97A !important; }
        .nv-score-low  { background: #2C2C2E !important; color: #98989D !important; }
        [data-testid="stSidebar"] {
            background: #2C2C2E !important;
            border-right-color: #38383A !important;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
            color: #F5F5F7 !important;
        }
        [data-baseweb="tag"] {
            background-color: #3A3A3C !important;
            color: #F5F5F7 !important;
        }
        [data-baseweb="tag"] svg { color: #98989D !important; fill: #98989D !important; }
        [data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea,
        [data-baseweb="popover"], [data-baseweb="menu"] {
            background: #2C2C2E !important;
            color: #F5F5F7 !important;
            border-color: #38383A !important;
        }
        .stButton button {
            background: #2C2C2E !important;
            border-color: #38383A !important;
            color: #F5F5F7 !important;
        }
        .stButton button:hover {
            background: #3A3A3C !important;
            border-color: #48484A !important;
        }
        .stCaption, [data-testid="stCaptionContainer"] { color: #98989D !important; }
        hr { border-color: #38383A !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
            )
            if remember:
                cookies.set(
                    "niels_session", expected_token,
                    expires_at=_dt.datetime.now() + _dt.timedelta(days=30),
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
        cookies.delete("niels_session")
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
    cols = st.columns(5)
    cols[0].metric("Vacatures", s.get("total") or 0)
    cols[1].metric("Nieuw", s.get("new_count") or 0)
    cols[2].metric("Favorieten", s.get("favorite_count") or 0)
    cols[3].metric("Gesolliciteerd", s.get("applied_count") or 0)
    cols[4].metric("Afgewezen", s.get("rejected_count") or 0)
    last_run = (s.get("last_run") or "—")[:16].replace("T", " ")
    st.caption(f"Laatst bijgewerkt: {last_run}")


def sidebar_filters() -> tuple[int, list[str], str, list[str], list[str], bool]:
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
        statuses = st.multiselect(
            "Status",
            options=STATUS_OPTIONS,
            default=["new"],
            format_func=lambda x: STATUS_LABELS[x],
        )
        favorites_only = st.checkbox("Alleen favorieten", value=False)
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
    return min_score, statuses, search, sources, provincies, favorites_only


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
    fav_icon = "🪵 ❤" if is_fav else "🤍"
    fav_help = "Verwijder uit favorieten" if is_fav else "Markeer als favoriet"

    with st.container(border=True):
        c1, c2 = st.columns([5, 1.6])
        with c1:
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
            b_l, b_r = st.columns([1, 1])
            with b_l:
                if st.button(fav_icon, key=f"fav_{row['id']}", help=fav_help, use_container_width=True):
                    toggle_favorite(int(row["id"]))
                    st.rerun()
            with b_r:
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
    min_score, statuses, search, sources, provincies, favorites_only = sidebar_filters()

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
