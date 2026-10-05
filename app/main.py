import sys
from pathlib import Path

# --- 1. PFAD-FIX ---
ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent

for p in (ROOT_DIR, APP_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st

# --- 2. SEITEN-KONFIGURATION (Einmalig und als allererster st.-Befehl) ---
st.set_page_config(
    page_title="Lagerverwaltung Suhring",
    page_icon="📦",
    layout="wide"
)

# --- 3. IMPORTE DER SERVICES ---
try:
    from app.services import lager_service
except ModuleNotFoundError:
    import lager_service

# --- 4. CACHING FÜR NEON POSTGRESQL ---
@st.cache_data(ttl=60, show_spinner="Verbinde mit Neon-Datenbank...")
def fetch_metrics():
    return lager_service.get_dashboard_metrics()

# --- 5. UI-AUFBAU ---
st.title("📦 Lagerverwaltung Suhring")
st.caption("Zentrale Erfassung, Fach-Inspektor & Werkzeugausleihe")

# Tiefenlink / QR-Code Scan vor Ort abfangen
params = st.query_params
qr_raum = params.get("raum", None)
qr_fach = params.get("fach", None)

if qr_raum and qr_fach:
    st.info(f"📍 **Direktaufruf erkannt:** Raum: **{qr_raum}** | Fach/Schrank: **{qr_fach}**")
    st.markdown("👉 Wechsle in der linken Seitenleiste auf **`4_Suche`**, um den Inhalt einzusehen.")
    st.divider()

# Dashboard-Zahlen abrufen
col1, col2, col3 = st.columns(3)

try:
    metrics = fetch_metrics()
    col1.metric("Erfasste Artikel", f"{metrics['gesamt_artikel']} Stk.")
    col2.metric("Aktuell verliehen", f"{metrics['aktive_leihe']} Gegenstände")
    col3.metric("Lagerorte", metrics["gesamt_orte"])
except Exception as e:
    col1.metric("Erfasste Artikel", "-")
    col2.metric("Aktuell verliehen", "-")
    col3.metric("Lagerorte", "-")
    st.warning(f"Datenbank wird synchronisiert oder antwortet verzögert: {e}")

st.divider()

st.subheader("Schnellzugriff über die Seitenleiste:")
st.markdown("""
* **1_Dashboard:** Systemüberblick & aktuelle Kennzahlen
* **2_Lagerplaetze:** Stellplätze ansehen & QR-Etiketten für Regale drucken
* **3_Artikel:** Neue Gegenstände erfassen, bearbeiten, verschieben oder löschen
* **4_Suche:** Volltextsuche & Fach-Inspektor für den QR-Scan vor Ort
* **5_Ausleihe:** Verleih von Werkzeugen & Kabeln verwalten
* **6_Bestand:** Zu- und Abgänge für die Lagerwirtschaft buchen
""")
