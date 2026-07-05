from __future__ import annotations

import sys
from pathlib import Path
from datetime import date

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.db.session import SessionLocal
from app.services.auth_service import require_login
from app.services.item_service import list_loanable_available_items
from app.services.loan_service import create_loan, list_open_loans, return_loan

st.set_page_config(page_title="Ausleihe", page_icon="🤝", layout="wide")

st.title("Ausleihe")

with SessionLocal() as session:
    available_items = list_loanable_available_items(session)
    open_loans = list_open_loans(session)

st.subheader("Neue Ausleihe")

if not available_items:
    st.info("Keine ausleihbaren verfuegbaren Artikel vorhanden.")
else:
    item_options = {}
    for item in available_items:
        label = (
            f"{item.name} | {item.location.room.name} | "
            f"{item.location.locationtype.value} | {item.location.label}"
        )
        item_options[label] = item.id

    with st.form("loan_form", clear_on_submit=True):
        selected_item_label = st.selectbox(
            "Artikel",
            options=list(item_options.keys()),
        )
        borrowername = st.text_input("Name")
        loandate = st.date_input("Ausleihdatum", value=date.today())

        submitted = st.form_submit_button("Ausleihe speichern", use_container_width=True)

        if submitted:
            try:
                with SessionLocal() as session:
                    create_loan(
                        session=session,
                        itemid=item_options[selected_item_label],
                        borrowername=borrowername,
                        loandate=loandate,
                    )
                st.success("Ausleihe wurde gespeichert.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

st.divider()
st.subheader("Offene Ausleihen")

if not open_loans:
    st.info("Keine offenen Ausleihen vorhanden.")
else:
    for loan in open_loans:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Artikel:** {loan.item.name}")
                st.write(f"**Name:** {loan.borrowername}")
                st.write(f"**Ausleihdatum:** {loan.loandate.isoformat()}")
                st.write(
                    f"**Lagerort:** {loan.item.location.room.name} / "
                    f"{loan.item.location.locationtype.value} / "
                    f"{loan.item.location.label}"
                )

            with col2:
                return_date = st.date_input(
                    "Rueckgabedatum",
                    value=date.today(),
                    key=f"return_date_{loan.id}",
                )
                if st.button("Rueckgabe buchen", key=f"return_btn_{loan.id}"):
                    try:
                        with SessionLocal() as session:
                            return_loan(
                                session=session,
                                loanid=loan.id,
                                returndate=return_date,
                            )
                        st.success(f"Rueckgabe fuer {loan.item.name} gebucht.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
