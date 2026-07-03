from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.db.models import LocationType
from app.db.session import SessionLocal
from app.services.auth_service import require_login
from app.services.location_service import create_location, list_locations
from app.services.room_service import list_rooms

st.set_page_config(page_title="Lagerplaetze", page_icon="📍", layout="wide")

if not require_login():
    st.warning("Bitte zuerst anmelden.")
    st.stop()

st.title("Lagerplaetze")

with SessionLocal() as session:
    rooms = list_rooms(session)
    locations = list_locations(session)

room_options = {room.name: room.id for room in rooms}

with st.form("location_form", clear_on_submit=True):
    st.subheader("Neuen Lagerplatz anlegen")

    selected_room_name = st.selectbox("Raum", options=list(room_options.keys()))
    selected_type = st.selectbox(
        "Typ",
        options=[LocationType.SCHRANK.value, LocationType.FACH.value],
    )
    label = st.text_input("Schranknummer oder Fachnummer")
    note = st.text_area("Notiz", height=80)

    submitted = st.form_submit_button("Speichern", use_container_width=True)

    if submitted:
        if not label.strip():
            st.error("Bitte eine Schranknummer oder Fachnummer eingeben.")
        else:
            with SessionLocal() as session:
                try:
                    create_location(
                        session=session,
                        roomid=room_options[selected_room_name],
                        locationtype=LocationType(selected_type),
                        label=label.strip(),
                        note=note.strip() or None,
                    )
                    st.success("Lagerplatz wurde angelegt.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

st.divider()
st.subheader("Vorhandene Lagerplaetze")

if not locations:
    st.info("Noch keine Lagerplaetze vorhanden.")
else:
    filter_room = st.selectbox(
        "Nach Raum filtern",
        options=["Alle"] + list(room_options.keys()),
    )

    filtered_locations = []
    for location in locations:
        room_name = location.room.name
        if filter_room == "Alle" or room_name == filter_room:
            filtered_locations.append(location)

    rows = []
    for location in filtered_locations:
        rows.append(
            {
                "Raum": location.room.name,
                "Typ": location.locationtype.value,
                "Nummer": location.label,
                "Notiz": location.note or "",
            }
        )

    st.dataframe(rows, use_container_width=True, hide_index=True)
