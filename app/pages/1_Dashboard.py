import streamlit as st
from app.services import lager_service

st.set_page_config(
    page_title="Lager-Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Lager-Cockpit")
st.caption("Echtzeit-Übersicht deiner Bestände und aktuellen Ausleihen")

# Kennzahlen direkt aus Neon abrufen
try:
    metrics = lager_service.get_dashboard_metrics()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Gesamtzahl Artikel", f"{metrics['gesamt_artikel']} Stk.")
    col2.metric("Aktuell verliehen", f"{metrics['aktive_leihe']} Gegenstände", delta_color="inverse")
    col3.metric("Erfasste Lagerorte", metrics["gesamt_orte"])
except Exception as e:
    st.error(f"Fehler beim Laden der Kennzahlen: {e}")

st.divider()

# Zwei Spalten: Aktive Ausleihen & Schnellnavigation
col_leihe, col_raeume = st.columns([3, 2])

with col_leihe:
    st.subheader("🔴 Aktuell verliehene Werkzeuge & Kabel")
    try:
        aktive_leihen = lager_service.get_aktive_ausleihen()
        if aktive_leihen:
            for leihe in aktive_leihen:
                st.warning(
                    f"**{leihe['item_name']}** ➔ Verliehen an **{leihe['person']}** (seit {leihe['datum_ausgabe']})"
                )
        else:
            st.success("🟢 Alle Werkzeuge und Kabel sind im Lager verfügbar!")
    except Exception as e:
        st.info("Noch keine Ausleihen registriert.")

with col_raeume:
    st.subheader("📍 Räume im System")
    st.markdown("""
    * **Halle:** Großgeräte, Maschinen & Baumaterial
    * **Werkstatt:** Handwerkzeuge, Messgeräte & Kleinteile
    * **EVA:** Elektroinstallation, Verteiler & Zubehör
    * **Honigraum:** Imkerei-Equipment, Gläser & Zubehör
    """)
    st.info("💡 **Tipp:** Wechsle auf **`2_Lagerplaetze`**, um neue QR-Codes für deine Regale und Schränke auszudrucken.")
