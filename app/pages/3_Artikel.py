from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import date
from decimal import Decimal

import streamlit as st

from app.core.formatters import format_item_row
from app.db.session import SessionLocal
from app.services.auth_service import require_login
from app.services.item_service import create_item, list_items
from app.services.location_service import list_locations

st.set_page_config(page_title="Artikel", page_icon="📦", layout="wide")

if not require_login():
    st.warning("Bitte zuerst anmelden.")
    st.stop()

st.title("Artikel")

with SessionLocal() as session:
    locations = list_locations(session)
    items = list_items(session)

if not locations:
    st.info("Bitte zuerst mindestens einen Lagerplatz anlegen.")
    st.stop()

location_options = {}
for location in locations:
    label = f"{location.room.name} | {location.locationtype.value} | {location.label}"
    location_options[label] = location.id

with st.form("item_form", clear_on_submit=True):
    st.subheader("Neuen Artikel anlegen")

    selected_location_label = st.selectbox(
        "Lagerplatz",
        options=list(location_options.keys()),
    )
    name = st.text_input("Artikelname")
    quantity = st.number_input("Menge", min_value=0.0, value=0.0, step=1.0)
    unit = st.text_input("Einheit", placeholder="z.B. Stk, m, Rolle")
    note = st.text_area("Notiz", height=80)

    expiry_enabled = st.checkbox("Haltbarkeitsdatum setzen")
    expirydate = None
    if expiry_enabled:
        expirydate = st.date_input("Haltbarkeitsdatum", value=date.today())

    isloanable = st.checkbox("Ausleihbar")

    is_cable = st.checkbox("Artikel ist ein Kabel")
    cabletype = None
    cablelengthmeter = None
    if is_cable:
        cabletype = st.text_input("Kabeltyp", placeholder="z.B. CAT7, H07RN-F")
        cablelengthmeter = st.number_input(
            "Kabellaenge in Meter",
            min_value=0.0,
            value=0.0,
            step=1.0,
        )

    submitted = st.form_submit_button("Speichern", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Bitte einen Artikelnamen eingeben.")
        else:
            with SessionLocal() as session:
                create_item(
                    session=session,
                    locationid=location_options[selected_location_label],
                    name=name.strip(),
                    quantity=Decimal(str(quantity)),
                    unit=unit.strip() or None,
                    note=note.strip() or None,
                    expirydate=expirydate if expiry_enabled else None,
                    isloanable=isloanable,
                    cabletype=cabletype.strip() if cabletype else None,
                    cablelengthmeter=Decimal(str(cablelengthmeter)) if is_cable else None,
                )
            st.success("Artikel wurde angelegt.")
            st.rerun()

st.divider()
st.subheader("Vorhandene Artikel")

if not items:
    st.info("Noch keine Artikel vorhanden.")
else:
    rows = [format_item_row(item) for item in items]
    st.dataframe(rows, use_container_width=True, hide_index=True)
