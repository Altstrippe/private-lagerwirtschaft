import streamlit as st
import pandas as pd
from datetime import date
from app.services import lager_service

st.set_page_config(
    page_title="Lagerbestand & Buchungen",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Lagerbestand: Zu- & Abgang")
st.caption("Bestandsveränderungen dokumentieren und Buchungshistorie einsehen.")

tab_buchen, tab_historie, tab_uebersicht = st.tabs([
    "📝 Buchung erfassen",
    "📜 Buchungshistorie",
    "📊 Aktuelle Bestandsliste"
])

# =============================================================
# TAB 1: BUCHUNG ERFASSEN
# =============================================================
with tab_buchen:
    artikel_liste = lager_service.get_lagerwirtschaft_artikel()

    if not artikel_liste:
        st.info("Es sind aktuell keine Artikel der Kategorie 'Lagerwirtschaft' vorhanden.")
    else:
        artikel_options = {
            f"{a['name']} (Bestand: {a['quantity']} {a['unit']})": a['id']
            for a in artikel_liste
        }

        col_art, col_typ = st.columns([2, 1])
        with col_art:
            ausgewaehlter_text = st.selectbox("Artikel auswählen *", list(artikel_options.keys()))
            artikel_id = artikel_options[ausgewaehlter_text]

        with col_typ:
            buchungs_typ = st.radio("Buchungsart *", ["Zugang", "Abgang"], horizontal=True)

        st.divider()

        col_m, col_d = st.columns([1, 1])
        with col_m:
            buchungs_menge = st.number_input("Menge *", min_value=0.1, value=1.0, step=1.0)
        with col_d:
            buchungs_datum = st.date_input("Buchungsdatum *", value=date.today(), format="DD.MM.YYYY")

        col_detail1, col_detail2 = st.columns([1, 1])

        if buchungs_typ == "Zugang":
            with col_detail1:
                woher = st.text_input(
                    "Woher? (Lieferant / Herkunft) *",
                    placeholder="z. B. Hornbach, Imkerbedarf Seip, Restposten"
                )
            with col_detail2:
                zweck_notiz = st.text_input(
                    "Zusatz / Beleg (optional)",
                    placeholder="z. B. Lieferschein-Nr., Sonderposten"
                )
        else:
            with col_detail1:
                woher = st.text_input(
                    "Wohin? (Einsatzort / Empfänger) *",
                    placeholder="z. B. Bienenstand Wald, Werkstatt Halle, Sabine"
                )
            with col_detail2:
                zweck_notiz = st.text_input(
                    "Verwendungszweck *",
                    placeholder="z. B. Erweiterung Zargen, Reparatur Dach"
                )

        st.divider()

        if st.button(f"💾 {buchungs_typ} verbindlich verbuchen", type="primary"):
            if not woher.strip():
                feld_name = "Woher" if buchungs_typ == "Zugang" else "Wohin"
                st.error(f"Bitte gib an, '{feld_name}' die Ware geht bzw. kommt.")
            elif buchungs_typ == "Abgang" and not zweck_notiz.strip():
                st.error("Bitte gib bei einem Abgang den Verwendungszweck an.")
            else:
                ok, msg, neuer_bestand = lager_service.buche_lagerbewegung(
                    item_id_str=artikel_id,
                    typ=buchungs_typ,
                    menge=buchungs_menge,
                    datum=buchungs_datum,
                    quelle_ziel=woher,
                    zweck=zweck_notiz,
                )
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

# =============================================================
# TAB 2: BUCHUNGSHISTORIE
# =============================================================
with tab_historie:
    st.subheader("Protokoll aller Lagerbewegungen")

    alle_artikel_fuer_filter = lager_service.get_lagerwirtschaft_artikel()
    filter_optionen = ["Alle Artikel"] + [a["name"] for a in alle_artikel_fuer_filter]
    gewaehlter_filter = st.selectbox("Historie filtern nach:", filter_optionen)

    filter_id = None
    if gewaehlter_filter != "Alle Artikel":
        match = next((a["id"] for a in alle_artikel_fuer_filter if a["name"] == gewaehlter_filter), None)
        filter_id = match

    historie_daten = lager_service.get_lagerbewegungen_historie(item_id_str=filter_id)

    if not historie_daten:
        st.info("Noch keine dokumentierten Buchungen für diese Auswahl vorhanden.")
    else:
        df_hist = pd.DataFrame(historie_daten)
        st.dataframe(df_hist, use_container_width=True, hide_index=True)

# =============================================================
# TAB 3: BESTANDSLISTE
# =============================================================
with tab_uebersicht:
    st.subheader("Aktuelle Bestände (Lagerwirtschaft)")
    aktuelle_artikel = lager_service.get_lagerwirtschaft_artikel()

    if aktuelle_artikel:
        tabelle = [
            {"Artikel": a["name"], "Bestand": f"{a['quantity']} {a['unit']}"}
            for a in aktuelle_artikel
        ]
        st.dataframe(pd.DataFrame(tabelle), use_container_width=True, hide_index=True)
    else:
        st.info("Keine Bestände vorhanden.")
