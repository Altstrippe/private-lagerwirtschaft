import streamlit as st
from app.core.config import RAEUME
from app.services import lager_service

st.set_page_config(page_title="Artikel anlegen", page_icon="📥", layout="wide")

st.title("📥 Neuen Artikel einsortieren")
st.caption("Erfasse neue Gegenstände und weise ihnen einen festen Stellplatz zu.")

with st.form("artikel_anlegen_form", clear_on_submit=True):
    st.subheader("1. Standort festlegen")
    col_raum, col_typ = st.columns(2)
    
    with col_raum:
        raum = st.selectbox("Raum", RAEUME)
    with col_typ:
        lagertyp = st.radio("Lagertyp", ["Regal", "Schrank"], horizontal=True)

    col_nr, col_box = st.columns(2)
    with col_nr:
        nummer = st.text_input(
            f"{lagertyp}nummer / Fachbezeichnung *", 
            placeholder="z. B. Fach 26 oder Schrank A"
        )
    
    with col_box:
        box_bezeichnung = ""
        if lagertyp == "Regal":
            hat_box = st.checkbox("Befinden sich in diesem Fach Boxen/Kisten?")
            if hat_box:
                box_bezeichnung = st.text_input(
                    "Box-Kennzeichnung", 
                    placeholder="z. B. Box 1 oder Kleinteilebox B"
                )

    st.divider()

    st.subheader("2. Artikel-Eigenschaften")
    col_name, col_kat = st.columns([2, 1])
    
    with col_name:
        artikel_name = st.text_input(
            "Bezeichnung des Artikels / Werkzeugs *", 
            placeholder="z. B. Drehmomentschlüssel, Honiggläser 500g, Mantelleitung"
        )
    with col_kat:
        kategorie = st.selectbox(
            "Kategorie", 
            ["Lagerwirtschaft", "Werkzeug", "Kabel"]
        )

    hat_foto = st.checkbox("📸 Foto zum Artikel vorhanden?")

    st.write("")
    submitted = st.form_submit_button("Artikel verbindlich speichern", type="primary")

    if submitted:
        if not artikel_name.strip() or not nummer.strip():
            st.error("Bitte gib mindestens den Artikelnamen und die Fach-/Schranknummer an.")
        else:
            try:
                lager_service.add_artikel(
                    raum=raum,
                    typ=lagertyp,
                    nummer=nummer.strip(),
                    box=box_bezeichnung.strip(),
                    name=artikel_name.strip(),
                    kategorie=kategorie,
                    hat_foto=hat_foto
                )
                st.success(f"'{artikel_name}' wurde erfolgreich in '{raum}' ({lagertyp} {nummer}) gespeichert!")
                st.balloons()
            except Exception as e:
                st.error(f"Fehler beim Speichern in der Datenbank: {e}")
