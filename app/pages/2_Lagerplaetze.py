import streamlit as st
import urllib.parse
from app.core.config import RAEUME
from app.services import lager_service

st.set_page_config(page_title="Lagerplätze & QR-Etiketten", page_icon="🏷️", layout="wide")

st.title("🏷️ Stellplätze & QR-Etiketten drucken")
st.caption("Erstelle QR-Codes für deine Regale und Schränke zum direkten Scannen vor Ort.")

col_raum, col_fach = st.columns(2)

with col_raum:
    ausgewaehlter_raum = st.selectbox("1. Raum auswählen", RAEUME)

# Bereits vorhandene Fächer für den Raum laden
vorhandene_faecher = lager_service.get_faecher_for_raum(ausgewaehlter_raum)

with col_fach:
    auswahl_modus = st.radio("Fach-Eingabe", ["Vorhandenes Fach wählen", "Neues Fach eingeben"], horizontal=True)
    if auswahl_modus == "Vorhandenes Fach wählen" and vorhandene_faecher:
        fach_nummer = st.selectbox("Fach / Schrank", vorhandene_faecher)
    else:
        fach_nummer = st.text_input("Fachnummer / Bezeichnung (z. B. Fach 26, Schrank A)", placeholder="26")

app_url = st.text_input(
    "Adresse deiner Streamlit-App (aus der Browser-Adresszeile kopieren):",
    placeholder="https://deine-lager-app.streamlit.app"
)

st.write("")
if st.button("QR-Code generieren", type="primary"):
    if not fach_nummer.strip() or not app_url.strip():
        st.warning("Bitte gib sowohl die App-Adresse als auch eine Fachnummer an.")
    else:
        ziel_link = lager_service.create_qr_link(
            base_url=app_url.strip(),
            raum=ausgewaehlter_raum,
            fach=fach_nummer.strip()
        )
        
        # QR-Code online generieren (300x300 px)
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(ziel_link)}"
        
        st.divider()
        col_img, col_info = st.columns([1, 2])
        with col_img:
            st.image(qr_api_url, caption=f"{ausgewaehlter_raum} - {fach_nummer}", width=220)
        with col_info:
            st.success(f"QR-Code für **{ausgewaehlter_raum} ➔ {fach_nummer}** erstellt!")
            st.markdown(f"**Verknüpfter Direkt-Link:**\n`{ziel_link}`")
            st.info("💡 **Druck-Tipp:** Rechtsklick auf das Bild ➔ *Grafik kopieren* oder *Bild speichern unter...* und mit deinem Etikettendrucker ausdrucken.")
