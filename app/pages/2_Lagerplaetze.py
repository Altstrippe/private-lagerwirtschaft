import urllib.parse
import streamlit as st
from app.core.config import RAEUME
from app.services import lager_service

st.set_page_config(
    page_title="Lagerplätze & QR-Etiketten",
    page_icon="🏷️",
    layout="wide"
)

st.title("🏷️ Stellplätze & QR-Etiketten")
st.caption("Verwalte Regalfächer und erstelle scanbare QR-Codes für deine Regale und Schränke vor Ort.")

col_raum, col_modus = st.columns([1, 1])

with col_raum:
    selected_raum = st.selectbox("1. Raum auswählen", RAEUME)

with col_modus:
    modus = st.radio(
        "2. Fach-Modus",
        options=["Neues Fach anlegen & speichern", "Vorhandenes Fach wählen"],
        horizontal=True
    )

ziel_fach = None

# --- MODUS A: NEUES FACH ANLEGEN ---
if modus == "Neues Fach anlegen & speichern":
    st.subheader(f"Neuen Stellplatz in '{selected_raum}' anlegen")
    
    col_typ, col_bez, col_note = st.columns([1, 2, 2])
    with col_typ:
        typ_auswahl = st.selectbox("Typ", ["Fach", "Schrank"])
    with col_bez:
        neues_label = st.text_input("Nummer / Bezeichnung", placeholder="z. B. 11 oder Fach 26")
    with col_note:
        neue_notiz = st.text_input("Zusatz / Kiste (optional)", placeholder="z. B. Systainer Blau")

    if st.button("💾 Stellplatz in Datenbank speichern", type="primary"):
        if neues_label:
            success, msg = lager_service.add_location(
                room_name=selected_raum,
                label=neues_label,
                location_type="fach" if typ_auswahl == "Fach" else "schrank",
                note=neue_notiz
            )
            if success:
                st.success(msg)
                ziel_fach = neues_label.strip()
            else:
                st.warning(msg)
        else:
            st.error("Bitte gib eine Fachbezeichnung ein.")

# --- MODUS B: VORHANDENES FACH WÄHLEN ---
else:
    st.subheader(f"Vorhandene Stellplätze in '{selected_raum}'")
    vorhandene_faecher = lager_service.get_faecher_for_raum(selected_raum)

    if not vorhandene_faecher:
        st.info(f"Im Raum '{selected_raum}' sind noch keine Fächer gespeichert. Wähle oben 'Neues Fach anlegen & speichern'.")
    else:
        ziel_fach = st.selectbox("Vorhandenes Fach auswählen", vorhandene_faecher)

st.divider()

# --- QR-CODE GENERIERUNG ---
st.subheader("🖨️ QR-Code für Regalbeschriftung generieren")

# Ermittelt automatisch die aktuelle Browser-URL der App
base_app_url = st.text_input(
    "Adresse deiner Streamlit-App (aus der Browserzeile):",
    value="https://private-lagerwirtschaft-suhring.streamlit.app"
)

fach_fuer_qr = ziel_fach if ziel_fach else st.session_state.get("letztes_fach", "")

col_btn, col_preview = st.columns([1, 2])

with col_btn:
    qr_fach_input = st.text_input("Fach für den QR-Code:", value=fach_fuer_qr, placeholder="z. B. 11")
    generieren = st.button("QR-Code generieren", type="secondary")

if generieren or (qr_fach_input and ziel_fach):
    if not qr_fach_input.strip():
        st.warning("Bitte gib ein Fach an, für das der QR-Code generiert werden soll.")
    else:
        # Tiefenlink für den Fach-Inspektor bauen
        ziel_url = lager_service.create_qr_link(base_app_url, selected_raum, qr_fach_input.strip())
        
        # QR-Code Bild über Standard-API generieren (keine extra Python-Pakete nötig)
        encoded_data = urllib.parse.quote(ziel_url)
        qr_img_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_data}"

        with col_preview:
            st.markdown(f"### Etikett: **{selected_raum} — {qr_fach_input}**")
            st.image(qr_img_url, width=220, caption=f"Scan-Ziel: {ziel_url}")
            st.markdown(f"[🔗 Direktlink testen]({ziel_url})")

st.divider()

# --- TABELLE ALLER FÄCHER IM RAUM ---
with st.expander(f"📋 Alle registrierten Fächer in '{selected_raum}' anzeigen"):
    faecher_liste = lager_service.get_faecher_for_raum(selected_raum)
    if faecher_liste:
        st.write(faecher_liste)
    else:
        st.write("Noch keine Fächer eingetragen.")
