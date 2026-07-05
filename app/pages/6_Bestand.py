from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.core.formatters import format_item_row
from app.db.session import SessionLocal
from app.services.auth_service import require_login
from app.services.item_service import list_stock_items
from app.services.room_service import list_rooms

st.set_page_config(page_title="Bestand", page_icon="📋", layout="wide")

st.title("Bestand")

with SessionLocal() as session:
    rooms = list_rooms(session)

room_names = ["Alle"] + [room.name for room in rooms]

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    selected_room = st.selectbox("Raum", options=["Alle", "Halle", "Werkstatt", "EVA", "Honigraum"])

with col2:
    only_loanable = st.checkbox("Nur ausleihbar")

with col3:
    only_on_loan = st.checkbox("Nur ausgeliehen")

with col4:
    only_with_expiry = st.checkbox("Nur mit Haltbarkeit")

with col5:
    only_household = st.checkbox("Nur Haushalt")

with col6:
    only_cables = st.checkbox("Nur Kabel")

with SessionLocal() as session:
    items = list_stock_items(
        session=session,
        room_name=selected_room,
        only_loanable=only_loanable,
        only_on_loan=only_on_loan,
        only_with_expiry=only_with_expiry,
        only_household=only_household,
        only_cables=only_cables,
    )

st.subheader("Gesamter Lagerbestand")

if not items:
    st.info("Keine Artikel fuer den aktuellen Filter gefunden.")
else:
    rows = [format_item_row(item) for item in items]

    metric_col1, metric_col2 = st.columns(2)
    with metric_col1:
        st.metric("Artikelpositionen", len(items))
    with metric_col2:
        st.metric("Gefilterter Raum", selected_room)

    st.dataframe(rows, use_container_width=True, hide_index=True)
