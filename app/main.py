from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.auth_service import ensure_session_state, login, logout

settings = get_settings()

st.set_page_config(
    page_title=settings.app_title,
    page_icon="📦",
    layout="wide",
)

ensure_session_state()

if not st.session_state.authenticated:
    st.title(settings.app_title)
    st.subheader("Login")

    username = st.text_input("Benutzername")
    password = st.text_input("Passwort", type="password")

    if st.button("Anmelden", use_container_width=True):
        with SessionLocal() as session:
            ok = login(session, username, password)

        if ok:
            st.rerun()
        else:
            st.error("Benutzername oder Passwort ist falsch.")
else:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(settings.app_title)
    with col2:
        if st.button("Abmelden", use_container_width=True):
            logout()
            st.rerun()

    st.success(f"Angemeldet als {st.session_state.username}.")
    st.info("Bitte waehle links eine Seite aus.")
