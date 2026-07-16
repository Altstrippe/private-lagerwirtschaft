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

if not require_login():
    st.warning("Bitte zuerst anmelden.")
    st.stop()

st.title("Bestand")

with SessionLocal() as session:
    rooms = list_rooms(session)

room_names = ["Alle"] + [room.name for room in rooms]

# Auf 7 Spalten erweitert für den neuen Werkzeug-Filter
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

with col1:
    # Hier nutzen wir jetzt die dynamische Raum-Liste aus der Datenbank
    selected_room = st.selectbox("Raum", options=room_names)

with col2:
    only_loanable = st.checkbox("Nur ausleihbar")

with col3:
    only_on_loan = st.checkbox("Nur ausgeliehen")

with col4:
    only_with_expiry = st.checkbox("Mit Haltbarkeit")

with col5:
    only_household = st.checkbox("Nur Haushalt")

with col6:
    only_tools = st.checkbox("Nur Werkzeug")  # <--- NEU: Werkzeug

with col7:
    only_cables = st.checkbox("Nur Kabel")

with SessionLocal() as session:
    items = list_stock_items(
        session=session,
        room_name=selected_room,
        only_loanable=only_loanable,
        only_on_loan=only_on_loan,
        only_with_expiry=only_with_expiry,
        only_household=only_household,
        only_tools=only_tools,        # <--- NEU: Filter an Logik übergeben
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

    # HIER IST DIE ÄNDERUNG: Tabelle klickbar machen und ID verstecken
    selection = st.dataframe(
        rows, 
        use_container_width=True, 
        hide_index=True,
        on_select="rerun",           # <--- Das macht die Zeilen klickbar
        selection_mode="single_row", # <--- Immer nur eine Zeile auswählbar
        column_config={
            "ID": None,              # <--- ID in der Tabelle unsichtbar machen
            "photolink": st.column_config.LinkColumn("📸 Foto", display_text="Anschauen 🔗")
        }
    )

    # WENN EINE ZEILE ANGEKLICKT WIRD, DETAILS ANZEIGEN:
    if len(selection.selection.rows) > 0:
        selected_index = selection.selection.rows[0]
        selected_item = items[selected_index]

        st.markdown("---")
        st.subheader(f"🏷️ Details: {selected_item.name}")
        
        detail_col1, detail_col2 = st.columns(2)
        with detail_col1:
            st.markdown(f"**Lagerort:** {selected_item.location.room.name} | {selected_item.location.locationtype.value} | {selected_item.location.label}")
            st.markdown(f"**Menge:** {float(selected_item.quantity)} {selected_item.unit or ''}")
            if selected_item.expirydate:
                st.markdown(f"**Haltbarkeit:** {selected_item.expirydate.isoformat()}")
            if selected_item.note:
                st.info(f"**Notiz:** {selected_item.note}")

        with detail_col2:
            st.markdown(f"**Werkzeug:** {'Ja' if selected_item.is_tool else 'Nein'}")
            st.markdown(f"**Haushalt:** {'Ja' if selected_item.ishousehold else 'Nein'}")
            st.markdown(f"**Ausleihbar:** {'Ja' if selected_item.isloanable else 'Nein'}")
            st.markdown(f"**Ausgeliehen:** {'Ja' if selected_item.isonloan else 'Nein'}")
            
            if selected_item.cabletype or selected_item.cablelengthmeter:
                st.markdown(f"**Kabel:** {selected_item.cabletype or '-'} ({float(selected_item.cablelengthmeter) if selected_item.cablelengthmeter else 0} m)")
            
            if selected_item.photolink:
                st.markdown(f"[📸 Foto in Dropbox öffnen]({selected_item.photolink})")