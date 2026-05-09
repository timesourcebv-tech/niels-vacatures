"""Streamlit-dashboard voor Niels.

Lokaal:        streamlit run dashboard.py
Online:        Streamlit Community Cloud — entrypoint = dashboard.py
"""
from __future__ import annotations

import datetime as _dt

import extra_streamlit_components as stx
import pandas as pd
import streamlit as st

from config import NIELS_PROFILE
from db import fetch_jobs, get_conn, stats, toggle_favorite, update_status

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

# Apple-geïnspireerde styling — clean, sans-serif, ruimtelijk
st.markdown(
    """
    <style>
    /* Globale typografie — Apple system fonts */
    html, body, [class*="css"], .stApp, [data-testid="stSidebar"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    h1, h2, h3, h4 {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif !important;
        letter-spacing: -0.022em;
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
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: #1D1D1F;
        margin: 0 0 0.4rem 0;
        line-height: 1.15;
    }
    .nv-header .nv-subtitle {
        color: #6E6E73;
        font-size: 1rem;
        font-weight: 400;
        margin: 0;
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
        padding: 0.32rem 0.85rem;
        border-radius: 980px;
        font-weight: 600;
        font-size: 0.82rem;
        letter-spacing: -0.01em;
        white-space: nowrap;
    }
    .nv-score-high { background: #E8F5E9; color: #1B5E20; }
    .nv-score-mid  { background: #FFF3E0; color: #B26A00; }
    .nv-score-low  { background: #F2F2F7; color: #6E6E73; }

    /* Vacature-titel */
    .nv-job-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #1D1D1F;
        margin: 0 0 0.25rem 0;
        line-height: 1.3;
        letter-spacing: -0.015em;
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
        font-size: 0.93rem;
        margin: 0 0 0.6rem 0;
    }
    .nv-job-meta strong {
        color: #1D1D1F;
        font-weight: 500;
    }
    .nv-job-meta .nv-source {
        color: #86868B;
        font-size: 0.78rem;
        margin-left: 0.5rem;
    }
    .nv-job-summary {
        color: #424245;
        font-size: 0.92rem;
        line-height: 1.55;
        margin: 0.35rem 0 0.4rem 0;
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
        font-size: 0.88rem;
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
        font-size: 0.83rem;
    }
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
        submitted = st.form_submit_button("Inloggen")
    if submitted:
        if user.strip().lower() == user_required.strip().lower() and pw == pw_required:
            cookies.set(
                "niels_username", user,
                expires_at=_dt.datetime.now() + _dt.timedelta(days=90),
            )
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Onjuiste gebruikersnaam of wachtwoord.")
    return False


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
        st.header("Filters")
        statuses = st.multiselect(
            "Status",
            options=STATUS_OPTIONS,
            default=["new"],
            format_func=lambda x: STATUS_LABELS[x],
        )
        favorites_only = st.checkbox("Alleen favorieten", value=False)

        provincies = st.multiselect(
            "Provincies",
            options=list(PROVINCIES.keys()),
            default=list(PROVINCIES.keys()),
            help="Vink provincies uit om vacatures uit die regio te verbergen",
        )
        min_score = 0

        with get_conn() as conn:
            sources_rows = conn.execute("SELECT DISTINCT source FROM jobs").fetchall()
        sources_all = sorted([r["source"] for r in sources_rows])
        sources = st.multiselect("Bronnen", sources_all, default=sources_all)

        search = st.text_input("Zoeken in titel/bedrijf", "")

        st.divider()
        with st.expander("Niels' profiel"):
            for line in NIELS_PROFILE["specialties"]:
                st.markdown(f"- {line}")
            st.markdown("**Talen**: " + ", ".join(NIELS_PROFILE["languages"]))
            st.markdown("**Locatie**: " + NIELS_PROFILE["location"])

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
            desc_raw = row.get("description")
            if desc_raw:
                desc = str(desc_raw).strip()
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
