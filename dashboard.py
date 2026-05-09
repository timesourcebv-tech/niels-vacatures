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
    page_title="Vacatures voor Niels",
    page_icon="🪵",
    layout="wide",
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

    st.title("🪵 Vacatures voor Niels")
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
    st.title("🪵 Vacatures voor Niels Hallingse")
    st.caption(
        f"Senior commerciële & leidinggevende rollen in de houtwereld — "
        f"{NIELS_PROFILE['experience_years']}+ jaar ervaring, "
        f"laatste functie {NIELS_PROFILE['career_history'][-1]}"
    )

    s = stats()
    cols = st.columns(5)
    cols[0].metric("Totaal", s.get("total") or 0)
    cols[1].metric("Nieuw", s.get("new_count") or 0)
    cols[2].metric("🪵 Favorieten", s.get("favorite_count") or 0)
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
        favorites_only = st.checkbox("🪵 Alleen favorieten", value=False)

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

    score_emoji = "🟢" if score >= 70 else ("🟡" if score >= 50 else "⚪")
    fav_icon = "🪵❤️" if is_fav else "🤍"
    fav_help = "Verwijder uit favorieten" if is_fav else "Voeg toe aan favorieten"

    with st.container(border=True):
        c1, c2 = st.columns([5, 2])
        with c1:
            st.markdown(f"### {score_emoji} [{title}]({row['url']})")
            st.markdown(
                f"**{company}** · {location} · "
                f"<sub>via {source} · {posted}</sub>",
                unsafe_allow_html=True,
            )
            desc_raw = row.get("description")
            if desc_raw:
                desc = str(desc_raw).strip()
                short = desc if len(desc) <= 280 else desc[:277].rsplit(" ", 1)[0] + "…"
                st.markdown(
                    f"<div style='color:#5B4A36;font-size:0.92rem;margin:0.3rem 0;'>{short}</div>",
                    unsafe_allow_html=True,
                )
                if len(desc) > 280:
                    with st.expander("Volledige beschrijving"):
                        st.write(desc)
        with c2:
            top_l, top_r = st.columns([1, 2])
            with top_l:
                if st.button(fav_icon, key=f"fav_{row['id']}", help=fav_help):
                    toggle_favorite(int(row["id"]))
                    st.rerun()
            with top_r:
                st.metric("Match", f"{score}/100", label_visibility="collapsed")
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
