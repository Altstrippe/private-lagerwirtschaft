import sys
from pathlib import Path

# --- 1. PFAD-FIX (Muss zwingend VOR allen anderen Importen stehen) ---
# Bindet das Repository-Hauptverzeichnis in den Python-Suchpfad ein:
ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent

for p in (ROOT_DIR, APP_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# --- 2. IMPORTE ---
import streamlit as st

st.set_page_config(page_title="Lagerverwaltung", layout="wide")
st.write("🟢 Python-Skript läuft...")

try:
    from app.services import lager_service
except ModuleNotFoundError:
    import lager_service

# --- 3. SEITEN-KONFIGURATION ---
st.set_page_config(
    page_title="Lagerverwaltung Suhring",
    page_icon="📦",
    layout="wide"
)

# Tiefenlink / QR-Code Scan vor Ort abfangen
params = st.query_params
qr_raum = params.get("raum", None)
qr_fach = params.get("fach", None)

st.title("📦 Lagerverwaltung Suhring")
st.caption("Zentrale Erfassung, Fach-Inspektor & Werkzeugausleihe")

# Schnellanzeige bei QR-Scan
if qr_raum and qr_fach:
    st.info(f"📍 **Direktaufruf erkannt:** Raum: **{qr_raum}** | Fach/Schrank: **{qr_fach}**")
    st.markdown("👉 Wechsle in der linken Seitenleiste auf **`4_Suche`**, um den Inhalt einzusehen.")
    st.divider()

# Dashboard-Zahlen direkt aus Neon abrufen
col1, col2, col3 = st.columns(3)

try:
    metrics = lager_service.get_dashboard_metrics()
    col1.metric("Erfasste Artikel", f"{metrics['gesamt_artikel']} Stk.")
    col2.metric("Aktuell verliehen", f"{metrics['aktive_leihe']} Gegenstände")
    col3.metric("Lagerorte", metrics["gesamt_orte"])
except Exception as e:
    st.warning(f"Datenbankverbindung wird initialisiert... ({e})")

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
