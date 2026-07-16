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
from app.services.item_service import search_items

st.set_page_config(page_title="Suche", page_icon="🔎", layout="wide")

st.title("Suche")

query = st.text_input(
    "Suchbegriff",
    placeholder="z.B. Schraub, Werkstatt, 101, CAT7",
)

if not query.strip():
    st.info("Bitte einen Suchbegriff eingeben.")
    st.stop()

with SessionLocal() as session:
    results = search_items(session, query)

st.subheader("Treffer")

if not results:
    st.warning("Keine Treffer gefunden.")
else:
    rows = [format_item_row(item) for item in results]
    
    # HIER IST DIE ÄNDERUNG: Tabelle klickbar machen und ID verstecken
    selection = st.dataframe(
        rows, 
        use_container_width=True,
        hide_index=True,
        on_select="rerun",           # <--- Das macht die Zeilen klickbar
        selection_mode="single_row", # <--- Man kann immer nur eine Zeile auswählen
        column_config={
            "ID": None,              # <--- ID in der Tabelle unsichtbar machen
            "photolink": st.column_config.LinkColumn("📸 Foto", display_text="Anschauen 🔗")
        }
    )

    # WENN EINE ZEILE ANGEKLICKT WIRD, DETAILS ANZEIGEN:
    if len(selection.selection.rows) > 0:
        selected_index = selection.selection.rows[0]
        selected_item = results[selected_index]

        st.markdown("---")
        st.subheader(f"🏷️ Details: {selected_item.name}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Lagerort:** {selected_item.location.room.name} | {selected_item.location.locationtype.value} | {selected_item.location.label}")
            st.markdown(f"**Menge:** {float(selected_item.quantity)} {selected_item.unit or ''}")
            if selected_item.expirydate:
                st.markdown(f"**Haltbarkeit:** {selected_item.expirydate.isoformat()}")
            if selected_item.note:
                st.info(f"**Notiz:** {selected_item.note}")

        with col2:
            st.markdown(f"**Werkzeug:** {'Ja' if selected_item.is_tool else 'Nein'}")
            st.markdown(f"**Haushalt:** {'Ja' if selected_item.ishousehold else 'Nein'}")
            st.markdown(f"**Ausleihbar:** {'Ja' if selected_item.isloanable else 'Nein'}")
            st.markdown(f"**Ausgeliehen:** {'Ja' if selected_item.isonloan else 'Nein'}")
            
            if selected_item.cabletype or selected_item.cablelengthmeter:
                st.markdown(f"**Kabel:** {selected_item.cabletype or '-'} ({float(selected_item.cablelengthmeter) if selected_item.cablelengthmeter else 0} m)")
            
            if selected_item.photolink:
                st.markdown(f"[📸 Foto in Dropbox öffnen]({selected_item.photolink})")f