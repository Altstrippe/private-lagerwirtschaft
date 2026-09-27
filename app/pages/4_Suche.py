import streamlit as st
import pandas as pd
from app.core.config import RAEUME
from app.services import lager_service

st.set_page_config(
    page_title="Lager-Auskunft & Suche",
    page_icon="🔍",
    layout="wide"
)

# -------------------------------------------------------------
# URL-PARAMETER PRÜFEN (QR-CODE DIREKTAUFRUF)
# -------------------------------------------------------------
params = st.query_params
qr_raum = params.get("raum", None)
qr_fach = params.get("fach", None)

st.title("🔍 Lager-Auskunft & Fach-Inspektor")
st.caption("Finde Artikel im Handumdrehen oder prüfe den Inhalt eines bestimmten Faches.")

tab_suche, tab_inspektor = st.tabs(["🔎 Volltextsuche über alle Bestände", "📍 Fach-Inspektor (QR-Scan)"])

# -------------------------------------------------------------
# TAB 1: VOLLTEXTSUCHE
# -------------------------------------------------------------
with tab_suche:
    col_suche, col_filter = st.columns([2, 1])
    with col_suche:
        suchbegriff = st.text_input(
            "Suchbegriff eingeben (Artikel, Fachnummer oder Kabeltyp):",
            placeholder="z. B. Dübel, 11, NYM, Kiste..."
        )
    with col_filter:
        raum_filter = st.selectbox("Raum eingrenzen:", ["Alle"] + RAEUME)

    try:
        artikel_liste = lager_service.get_all_articles_joined(
            search_term=suchbegriff.strip() if suchbegriff else None,
            raum_filter=raum_filter
        )

        if not artikel_liste:
            st.info("Keine passenden Artikel gefunden.")
        else:
            st.markdown(f"**Gefundene Treffer:** {len(artikel_liste)}")

            for art in artikel_liste:
                menge = art.get("quantity", art.get("bestand", 0.0))
                einheit = art.get("unit", "Stk.")
                box_text = f" | Box/Kiste: **{art['box']}**" if art.get("box") else ""
                
                with st.expander(f"📦 **{art['name']}** — Raum: {art['raum']} ({art['typ']} {art['nummer']})"):
                    col_info, col_status = st.columns([2, 1])
                    
                    with col_info:
                        st.markdown(f"**Kategorie:** {art['kategorie']}")
                        st.markdown(f"**Lagerort:** {art['raum']} ➔ {art['typ']} **{art['nummer']}**{box_text}")
                        st.markdown(f"**Bestand:** {menge} {einheit}")
                        
                        if art.get("photolink") and art["photolink"] != "vorhanden":
                            st.markdown(f"[📷 Foto zum Artikel ansehen]({art['photolink']})")

                    with col_status:
                        if art.get("isonloan"):
                            st.error(f"🔴 **Aktuell verliehen**\n\n{art.get('vermietung', '')}")
                        else:
                            st.success("🟢 **Verfügbar im Lager**")

    except Exception as e:
        st.error(f"Fehler bei der Suche: {e}")

# -------------------------------------------------------------
# TAB 2: FACH-INSPEKTOR
# -------------------------------------------------------------
with tab_inspektor:
    st.subheader("Inhalt eines Stellplatzes anzeigen")
    
    col_r, col_f = st.columns([1, 1])
    
    with col_r:
        default_raum_idx = RAEUME.index(qr_raum) if qr_raum in RAEUME else 0
        inspektor_raum = st.selectbox("Raum wählen", RAEUME, index=default_raum_idx)

    faecher_im_raum = lager_service.get_faecher_for_raum(inspektor_raum)
    
    with col_f:
        if faecher_im_raum:
            default_fach_idx = faecher_im_raum.index(qr_fach) if qr_fach in faecher_im_raum else 0
            inspektor_fach = st.selectbox("Fach / Schrank wählen", faecher_im_raum, index=default_fach_idx)
        else:
            inspektor_fach = st.text_input("Fachbezeichnung:", value=qr_fach if qr_fach else "")

    if inspektor_fach:
        try:
            fach_inhalt = lager_service.get_fach_inhalt(inspektor_raum, inspektor_fach)
            
            st.divider()
            st.markdown(f"### Aktueller Inhalt: **{inspektor_raum} — Fach {inspektor_fach}**")
            
            if not fach_inhalt:
                st.info("Dieses Fach ist aktuell leer (keine Artikel zugewiesen).")
            else:
                daten_tabelle = []
                for item in fach_inhalt:
                    status = "🔴 Verliehen" if item.get("isonloan") else "🟢 Im Fach"
                    daten_tabelle.append({
                        "Artikel": item["name"],
                        "Kategorie": item["kategorie"],
                        "Menge": f"{item['quantity']} {item['unit']}",
                        "Kiste / Box": item["box"] if item["box"] else "-",
                        "Status": status
                    })
                st.dataframe(pd.DataFrame(daten_tabelle), use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"Fehler beim Laden des Fachinhalts: {e}")
    else:
        st.info("Bitte wähle ein Fach aus, um den Inhalt einzusehen.")
