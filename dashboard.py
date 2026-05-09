"""Streamlit-dashboard voor Niels.

Lokaal:        streamlit run dashboard.py
Online:        Streamlit Community Cloud — entrypoint = dashboard.py
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from config import CITIES_BE_NL, CITIES_NEAR, CITIES_RANDSTAD, NIELS_PROFILE
from db import fetch_jobs, get_conn, stats, update_status

REGIONS = {
    "Alles": None,
    "Zaanstreek + omgeving": CITIES_NEAR,
    "Randstad": CITIES_RANDSTAD,
    "Nederland (totaal)": ["nederland", "netherlands"] + CITIES_NEAR + CITIES_RANDSTAD + [
        "noord-holland", "zuid-holland", "utrecht", "gelderland", "noord-brabant",
        "limburg", "overijssel", "drenthe", "groningen", "friesland", "zeeland", "flevoland",
        "eindhoven", "tilburg", "breda", "nijmegen", "arnhem", "enschede", "groningen",
        "maastricht", "venlo", "den bosch", "'s-hertogenbosch", "apeldoorn", "zwolle",
    ],
    "Vlaanderen / België": ["belgië", "belgie", "belgium", "vlaanderen", "flanders"] + CITIES_BE_NL,
}

st.set_page_config(
    page_title="Vacatures voor Niels",
    page_icon="🪵",
    layout="wide",
)

STATUS_LABELS = {
    "new": "Nieuw",
    "interesting": "Interessant",
    "applied": "Gesolliciteerd",
    "rejected": "Afgewezen",
}
STATUS_OPTIONS = list(STATUS_LABELS.keys())


# ──────────────────────────────────────────────────────────
# Login-gate via Streamlit secrets (username + wachtwoord)
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
    st.title("🪵 Vacatures voor Niels")
    with st.form("login"):
        user = st.text_input("Gebruikersnaam")
        pw = st.text_input("Wachtwoord", type="password")
        submitted = st.form_submit_button("Inloggen")
    if submitted:
        if user.strip().lower() == user_required.strip().lower() and pw == pw_required:
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
    cols[2].metric("Interessant", s.get("interesting_count") or 0)
    cols[3].metric("Gesolliciteerd", s.get("applied_count") or 0)
    cols[4].metric("Afgewezen", s.get("rejected_count") or 0)
    last_run = (s.get("last_run") or "—")[:16].replace("T", " ")
    st.caption(f"Laatst bijgewerkt: {last_run}")


def sidebar_filters() -> tuple[int, list[str], str, list[str], str]:
    with st.sidebar:
        st.header("Filters")
        statuses = st.multiselect(
            "Status",
            options=STATUS_OPTIONS,
            default=["new", "interesting"],
            format_func=lambda x: STATUS_LABELS[x],
        )

        region = st.selectbox("Regio", list(REGIONS.keys()), index=0)
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
    return min_score, statuses, search, sources, region


def render_job_card(row: pd.Series) -> None:
    status = row["status"]
    score = int(row["score"])
    title = row["title"]
    company = row["company"] or "Onbekend"
    location = row["location"] or "—"
    posted = str(row.get("posted_at") or row.get("discovered_at") or "")[:10]
    source = row["source"]

    score_emoji = "🟢" if score >= 70 else ("🟡" if score >= 50 else "⚪")

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
                # Toon eerste ~280 chars als compacte samenvatting onder bedrijfsregel
                short = desc if len(desc) <= 280 else desc[:277].rsplit(" ", 1)[0] + "…"
                st.markdown(
                    f"<div style='color:#5B4A36;font-size:0.92rem;margin:0.3rem 0;'>{short}</div>",
                    unsafe_allow_html=True,
                )
                # Volledige beschrijving als die langer is
                if len(desc) > 280:
                    with st.expander("Volledige beschrijving"):
                        st.write(desc)
            if row.get("notes"):
                st.info(f"📝 {row['notes']}")
        with c2:
            st.metric("Match", f"{score}/100")
            new_status = st.selectbox(
                "Status",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(status) if status in STATUS_OPTIONS else 0,
                format_func=lambda s: STATUS_LABELS[s],
                key=f"status_{row['id']}",
                label_visibility="collapsed",
            )
            notes = st.text_input(
                "Notitie",
                value=row.get("notes") or "",
                key=f"notes_{row['id']}",
                placeholder="Notitie...",
                label_visibility="collapsed",
            )
            current_notes = row.get("notes") or ""
            if new_status != status or notes != current_notes:
                if st.button("Opslaan", key=f"save_{row['id']}"):
                    update_status(int(row["id"]), new_status, notes or None)
                    st.rerun()


def main() -> None:
    if not login_gate():
        return

    header()
    min_score, statuses, search, sources, region = sidebar_filters()

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

    if sources:
        df = df[df["source"].isin(sources)]
    region_terms = REGIONS.get(region)
    if region_terms:
        loc_lower = df["location"].fillna("").str.lower()
        mask = pd.Series(False, index=df.index)
        for term in region_terms:
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
