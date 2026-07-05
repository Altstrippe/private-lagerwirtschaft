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
    
    # HIER IST DIE ÄNDERUNG: Die Tabelle bekommt die column_config für den Fotolink
    st.dataframe(
        rows, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "photolink": st.column_config.LinkColumn("📸 Foto", display_text="Anschauen 🔗")
        }
    )