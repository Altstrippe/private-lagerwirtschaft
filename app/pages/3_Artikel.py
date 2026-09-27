import streamlit as st
from app.core.config import RAEUME
from app.services import lager_service

st.set_page_config(
    page_title="Artikel einsortieren",
    page_icon="📥",
    layout="wide"
)

st.title("📥 Neuen Artikel einsortieren")
st.caption("Erfasse neue Gegenstände und weise ihnen einen festen Stellplatz zu.")

# -------------------------------------------------------------
# 1. STANDORT FESTLEGEN
# -------------------------------------------------------------
st.subheader("1. Standort festlegen")

col_raum, col_typ = st.columns([2, 1])
with col_raum:
    selected_raum = st.selectbox("Raum", RAEUME)

with col_typ:
    lagertyp = st.radio("Lagertyp", ["Regal", "Schrank"], horizontal=True)

# Vorhandene Fächer aus der Datenbank für den gewählten Raum laden
vorhandene_faecher = lager_service.get_faecher_for_raum(selected_raum)

col_fach, col_box = st.columns([2, 1])

with col_fach:
    # Auswahl: Vorhandenes Fach wählen oder neues eintippen
    if vorhandene_faecher:
        fach_optionen = ["-- Vorhandenes Fach wählen --"] + vorhandene_faecher + ["➕ Neues Fach / neue Schranknummer eingeben"]
        auswahl = st.selectbox("Regalnummer / Fachbezeichnung *", options=fach_optionen)
        
        if auswahl == "➕ Neues Fach / neue Schranknummer eingeben":
            fach_nummer = st.text_input("Neue Bezeichnung eingeben (z. B. Fach 11, Schrank B):")
        elif auswahl == "-- Vorhandenes Fach wählen --":
            fach_nummer = ""
        else:
            fach_nummer = auswahl
    else:
        st.info(f"Noch keine Fächer in '{selected_raum}' angelegt. Bitte neu eingeben:")
        fach_nummer = st.text_input("Regalnummer / Fachbezeichnung *", placeholder="z. B. Fach 11, Schrank A")

with col_box:
    hat_box = st.checkbox("Befinden sich in diesem Fach Boxen/Kisten?")
    box_bezeichnung = ""
    if hat_box:
        box_bezeichnung = st.text_input("Kisten- / Boxen-Label:", placeholder="z. B. Box Gelb, Systainer 3")

st.divider()

# -------------------------------------------------------------
# 2. ARTIKEL-EIGENSCHAFTEN
# -------------------------------------------------------------
st.subheader("2. Artikel-Eigenschaften")

col_name, col_kat = st.columns([2, 1])
with col_name:
    artikel_name = st.text_input(
        "Bezeichnung des Artikels / Werkzeugs *",
        placeholder="z. B. Drehmomentschlüssel, Honiggläser 500g, Mantelleitung NYM-J 3x1.5"
    )

with col_kat:
    kategorie = st.selectbox("Kategorie", ["Lagerwirtschaft", "Werkzeug", "Kabel"])

# Dynamische Zusatzfelder je nach Kategorie
menge = 1.0
einheit = "Stk."
mhd_datum = None
kabel_typ = None
kabel_laenge = None

if kategorie == "Lagerwirtschaft":
    col_m, col_e, col_mhd = st.columns([1, 1, 2])
    with col_m:
        menge = st.number_input("Anfangsbestand", min_value=0.0, value=1.0, step=1.0)
    with col_e:
        einheit = st.selectbox("Einheit", ["Stk.", "kg", "Liter", "Meter", "Paket"])
    with col_mhd:
        hat_mhd = st.checkbox("Mindesthaltbarkeitsdatum (MHD) erfassen?")
        if hat_mhd:
            mhd_datum = st.date_input("Haltbar bis", format="DD.MM.YYYY")

elif kategorie == "Werkzeug":
    col_m, col_e = st.columns([1, 1])
    with col_m:
        menge = st.number_input("Menge", min_value=1.0, value=1.0, step=1.0)
    with col_e:
        einheit = st.selectbox("Einheit", ["Stk.", "Set"])

elif kategorie == "Kabel":
    col_kt, col_kl = st.columns([2, 1])
    with col_kt:
        kabel_typ = st.text_input("Kabeltyp", placeholder="z. B. H07RN-F 5G2.5 oder NYM-J 3x1.5")
    with col_kl:
        kabel_laenge = st.number_input("Restlänge (in Metern)", min_value=0.0, value=50.0, step=5.0)
    menge = 1.0
    einheit = "Trommel/Ring"

# Foto-Verknüpfung
col_foto_check, col_foto_link = st.columns([1, 2])
with col_foto_check:
    hat_foto = st.checkbox("📷 Foto zum Artikel vorhanden?")

photolink_val = ""
with col_foto_link:
    if hat_foto:
        photolink_val = st.text_input(
            "Link zum Foto (URL / Cloud-Speicher):",
            placeholder="https://photos.app.goo.gl/... oder Bildlink"
        )

st.divider()

# -------------------------------------------------------------
# SPEICHERN
# -------------------------------------------------------------
if st.button("Artikel verbindlich speichern", type="primary"):
    if not fach_nummer or not fach_nummer.strip():
        st.error("Bitte wähle eine Fachbezeichnung aus oder gib eine neue ein.")
    elif not artikel_name or not artikel_name.strip():
        st.error("Bitte gib eine Bezeichnung für den Artikel ein.")
    else:
        try:
            lager_service.add_artikel(
                raum=selected_raum,
                typ=lagertyp,
                nummer=fach_nummer.strip(),
                box=box_bezeichnung.strip(),
                name=artikel_name.strip(),
                kategorie=kategorie,
                quantity=menge,
                unit=einheit,
                cabletype=kabel_typ,
                cablelengthmeter=kabel_laenge,
                hat_foto=hat_foto,
                photolink=photolink_val,
                expirydate=mhd_datum
            )
            st.success(f"✅ Artikel '{artikel_name}' wurde erfolgreich in Fach '{fach_nummer}' ({selected_raum}) gespeichert!")
            st.balloons()
        except Exception as e:
            st.error(f"Fehler beim Speichern in Neon: {e}")
