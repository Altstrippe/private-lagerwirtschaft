import streamlit as st
from app.core.config import RAEUME
from app.services import lager_service

st.set_page_config(page_title="Suche & Fach-Inspektor", page_icon="🔍", layout="wide")

# URL-Parameter für QR-Code-Scans auslesen
params = st.query_params
qr_raum = params.get("raum", None)
qr_fach = params.get("fach", None)

# Wenn per QR-Code geöffnet, Fach-Inspektor als Standard wählen
ist_qr_aufruf = bool(qr_raum and qr_fach)

st.title("🔍 Lager-Auskunft")

ansicht = st.radio(
    "Suchmodus", 
    ["📍 Fach-Inspektor (Exakter Stellplatz)", "🔎 Volltextsuche (Über alles)"], 
    horizontal=True,
    index=0 if ist_qr_aufruf else 1
)

st.divider()

# ==========================================
# MODUS 1: FACH-INSPEKTOR
# ==========================================
if ansicht.startswith("📍"):
    st.subheader("Fachinhalt prüfen")
    st.caption("Wähle einen Raum und ein Fach aus, um den exakten Inhalt ohne Streuverluste zu sehen.")

    col1, col2 = st.columns(2)
    with col1:
        default_raum_idx = RAEUME.index(qr_raum) if (qr_raum and qr_raum in RAEUME) else 0
        ausgewaehlter_raum = st.selectbox("1. Raum", RAEUME, index=default_raum_idx)

    # Alle tatsächlich existierenden Fächer im Raum aus dem Service abrufen
    vorhandene_faecher = lager_service.get_faecher_for_raum(ausgewaehlter_raum)

    with col2:
        default_fach_idx = 0
        if qr_fach and str(qr_fach) in vorhandene_faecher:
            default_fach_idx = vorhandene_faecher.index(str(qr_fach))
            
        ausgewaehltes_fach = st.selectbox(
            "2. Fach- oder Schranknummer", 
            vorhandene_faecher if vorhandene_faecher else ["(Keine Fächer eingetragen)"],
            index=default_fach_idx
        )

    if ausgewaehltes_fach and ausgewaehltes_fach != "(Keine Fächer eingetragen)":
        inhalt = lager_service.get_fach_inhalt(ausgewaehlter_raum, ausgewaehltes_fach)
        
        st.write("")
        st.markdown(f"### Aktueller Inhalt: **{ausgewaehlter_raum} ➔ {ausgewaehltes_fach}**")
        
        if inhalt:
            for item in inhalt:
                box_hinweis = f"📦 In: **{item['box']}**" if item['box'] else "Frei im Fach (keine Box)"
                st.success(f"**{item['name']}** ({item['kategorie']}) | {box_hinweis}")
        else:
            st.info("Dieses Fach ist laut Datenbank derzeit leer.")

# ==========================================
# MODUS 2: VOLLTEXTSUCHE
# ==========================================
else:
    st.subheader("Globale Suche über alle Räume")
    
    col_suche, col_filter = st.columns([2, 1])
    with col_suche:
        suchbegriff = st.text_input("Gegenstand, Kabel oder Werkzeug suchen...", placeholder="z. B. Bohrer, 26, NYM")
    with col_filter:
        raum_filter = st.selectbox("Auf Raum eingrenzen", ["Alle"] + RAEUME)

    ergebnisse = lager_service.get_all_articles_joined(
        search_term=suchbegriff.strip() if suchbegriff else None,
        raum_filter=raum_filter
    )

    st.write("")
    if ergebnisse:
        st.markdown(f"**Gefundene Einträge:** {len(ergebnisse)}")
        for art in ergebnisse:
            box_text = f" (Box: {art['box']})" if art['box'] else ""
            foto_status = "📸 Foto" if art['hat_foto'] else "Kein Foto"
            
            # Zusätzliche Details abhängig von der Kategorie
            extra_info = ""
            if art['bestand'] is not None:
                extra_info += f" | Bestand: **{art['bestand']} Stk.**"
            if art['vermietung']:
                extra_info += f" | 🔴 **{art['vermietung']}**"
            elif art['kategorie'] in ["Werkzeug", "Kabel"]:
                extra_info += " | 🟢 **Verfügbar**"

            st.info(
                f"**{art['name']}** ({art['kategorie']}) ➔ **{art['raum']}** ({art['typ']} {art['nummer']}{box_text}) "
                f"| {foto_status}{extra_info}"
            )
    else:
        st.warning("Keine passenden Artikel gefunden.")
