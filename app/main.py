from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.core.config import get_settings

settings = get_settings()

st.set_page_config(
    page_title=settings.app_title,
    page_icon="📦",
    layout="wide",
)

# Login-Logik komplett entfernt
col1, col2 = st.columns([4, 1])
with col1:
    st.title(settings.app_title)
with col2:
    # Optional: Den Abmelden-Button kannst du hier auch entfernen, 
    # da du ja keinen Login mehr hast.
    pass 

st.info("Willkommen in deiner Lagerverwaltung. Bitte wähle links eine Seite aus.")