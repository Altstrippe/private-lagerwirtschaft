from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.db.session import SessionLocal
from app.services.auth_service import require_login
from app.services.dashboard_service import get_dashboard_stats

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")

if not require_login():
    st.warning("Bitte zuerst anmelden.")
    st.stop()

st.title("Dashboard")
st.caption("Schnellueberblick ueber deine private Lagerwirtschaft")

with SessionLocal() as session:
    stats = get_dashboard_stats(session)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Lagerplaetze", stats["location_count"])

with col2:
    st.metric("Artikelpositionen", stats["item_count"])

with col3:
    st.metric("Offene Ausleihen", stats["open_loan_count"])

with col4:
    st.metric("Artikel mit Haltbarkeit", stats["expiry_count"])

st.divider()

st.subheader("Schnellzugriff")

nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    st.page_link("pages/2_Lagerplaetze.py", label="Zu den Lagerplaetzen", icon="📍")

with nav_col2:
    st.page_link("pages/4_Suche.py", label="Zur Suche", icon="🔎")

with nav_col3:
    st.page_link("pages/6_Bestand.py", label="Zum Bestand", icon="📋")

st.divider()

st.subheader("Hinweise")

hint_col1, hint_col2 = st.columns(2)

with hint_col1:
    st.info(
        "Neue Lagerplaetze zuerst unter 'Lagerplaetze' anlegen, "
        "danach Artikel zuordnen."
    )

with hint_col2:
    st.info(
        "Die globale Suche findet Teiltreffer in Artikelnamen, Raum, "
        "Schranknummer, Fachnummer und Kabeltyp."
    )
