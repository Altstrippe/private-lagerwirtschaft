import streamlit as st
from app.services import lager_service

st.set_page_config(
    page_title="Lagerverwaltung Suhring",
    page_icon="📦",
    layout="wide"
)

# Prüfen, ob die App über einen QR-Code mit Parametern geöffnet wurde
params = st.query_params
qr_raum = params.get("raum", None)
qr_fach = params.get("fach", None)

st.title("📦 Lagerverwaltung Suhring")
st.caption("Zentrale Erfassung, Fach-Inspektor & Werkzeugausleihe")

# Schnell-Status bei QR-Scan
if qr_raum and qr_fach:
    st.info(f"📍 **Direktaufruf erkannt:** Raum: **{qr_raum}** | Fach/Schrank: **{qr_fach}**")
    st.markdown("👉 Wechsle in der linken Seitenleiste auf **`4_Suche`**, um den exakten Fachinhalt einzusehen.")
    st.divider()

# Dashboard-Übersicht
col1, col2, col3 = st.columns(3)

try:
    metrics = lager_service.get_dashboard_metrics()
    col1.metric("Erfasste Artikel", metrics["gesamt_artikel"])
    col2.metric("Aktuell verliehen", metrics["aktive_leihe"])
    col3.metric("Lagerbewegungen", metrics["bewegungen"])
except Exception as e:
    st.warning("Verbindung zur Datenbank wird aufgebaut oder noch initialisiert...")

st.divider()

st.subheader("Schnellzugriff über die Seitenleiste:")
st.markdown("""
* **1_Dashboard:** Kennzahlen und Systemübersicht[cite: 2]
* **2_Lagerplaetze:** QR-Code-Etiketten für Regalböden generieren und drucken[cite: 2]
* **3_Artikel:** Neue Gegenstände und Werkzeuge einsortieren[cite: 2]
* **4_Suche:** Volltextsuche und Fach-Inspektor vor Ort am Regal[cite: 2]
* **5_Ausleihe:** Verleih von Kabeln & Werkzeugen mit Aus- und Rückgabedatum[cite: 2]
* **6_Bestand:** Zu- und Abgänge für die Lagerwirtschaft erfassen[cite: 2]
""")
