from __future__ import annotations

import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.db.models import User


def ensure_session_state() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "username" not in st.session_state:
        st.session_state.username = None


def login(session: Session, username: str, password: str) -> bool:
    user = session.scalar(select(User).where(User.username == username))
    if user is None:
        return False

    if not verify_password(password, user.passwordhash):
        return False

    st.session_state.authenticated = True
    st.session_state.username = user.username
    return True


def logout() -> None:
    st.session_state.authenticated = False
    st.session_state.username = None


def require_login() -> bool:
    ensure_session_state()
    return st.session_state.authenticated
