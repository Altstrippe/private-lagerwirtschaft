from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import date
from decimal import Decimal

import streamlit as st

from app.core.formatters import format_item_row
from app.db.session import SessionLocal
from app.services.auth_service import require_login
from app.services.item_service import create_item, list_items, update_item, delete_item
from app.services.location_service import list_locations

st.set_page_config(page_title="Artikel", page_icon="📦", layout="wide")

st.title("Artikel")

with SessionLocal() as session:
    locations = list_locations(session)
    items = list_items(session)

if not locations:
    st.info("Bitte zuerst mindestens einen Lagerplatz anlegen.")
    st.stop()

# Lagerplatz-Optionen vorbereiten (wird für beide Tabs gebraucht)
location_options = {}
for location in locations:
    label = f"{location.room.name} | {location.locationtype.value} | {location.label}"
    location_options[label] = location.id

# TABS ERSTELLEN
tab_neu, tab_bearbeiten = st.tabs(["➕ Artikel anlegen", "✏️ Artikel bearbeiten"])

# ==========================================
# TAB 1: NEUEN ARTIKEL ANLEGEN
# ==========================================
with tab_neu:
    with st.form("item_form", clear_on_submit=True):
        st.subheader("Neuen Artikel anlegen")

        selected_location_label = st.selectbox(
            "Lagerplatz",
            options=list(location_options.keys()),
        )
        name = st.text_input("Artikelname")
        quantity = st.number_input("Menge", min_value=0.0, value=0.0, step=1.0)
        unit = st.text_input("Einheit", placeholder="z.B. Stk, m, Rolle")
        note = st.text_area("Notiz", height=80)
        
        # --- NEU: Foto-Link Eingabe ---
        photolink = st.text_input("🔗 Dropbox Foto-Link (Optional)", placeholder="https://www.dropbox.com/...")

        expiry_enabled = st.checkbox("Haltbarkeitsdatum setzen")
        expirydate = None
        if expiry_enabled:
            expirydate = st.date_input("Haltbarkeitsdatum", value=date.today())

        isloanable = st.checkbox("Ausleihbar")
        ishousehold = st.checkbox("Haushaltsartikel")
        is_cable = st.checkbox("Artikel ist ein Kabel")
        
        cabletype = None
        cablelengthmeter = None
        if is_cable:
            cabletype = st.text_input("Kabeltyp", placeholder="z.B. CAT7, H07RN-F")
            cablelengthmeter = st.number_input(
                "Kabellaenge in Meter",
                min_value=0.0,
                value=0.0,
                step=1.0,
            )

        submitted = st.form_submit_button("Speichern", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("Bitte einen Artikelnamen eingeben.")
            else:
                with SessionLocal() as db_session:
                    create_item(
                        session=db_session,
                        locationid=location_options[selected_location_label],
                        name=name.strip(),
                        quantity=Decimal(str(quantity)),
                        unit=unit.strip() or None,
                        note=note.strip() or None,
                        photolink=photolink.strip() or None,  # --- NEU: Foto-Link speichern ---
                        expirydate=expirydate if expiry_enabled else None,
                        isloanable=isloanable,
                        ishousehold=ishousehold,
                        cabletype=cabletype.strip() if cabletype else None,
                        cablelengthmeter=Decimal(str(cablelengthmeter)) if is_cable else None,
                    )
                st.success("Artikel wurde angelegt.")
                st.rerun()

# ==========================================
# TAB 2: ARTIKEL BEARBEITEN
# ==========================================
with tab_bearbeiten:
    if not items:
        st.info("Noch keine Artikel im System vorhanden.")
    else:
        st.subheader("Bestehenden Artikel ändern")
        # Dictionary für das Dropdown-Menü: "Name (ID: 12)" -> Item-Objekt
        item_options = {f"{item.name} (ID: {item.id})": item for item in items}
        
        # Welcher Artikel soll bearbeitet werden?
        selected_item_label = st.selectbox("Welchen Artikel möchtest du bearbeiten?", options=list(item_options.keys()))
        item_to_edit = item_options[selected_item_label]
        
        # Herausfinden, welcher Lagerplatz-Text dem aktuell hinterlegten Ort entspricht
        old_location_label = list(location_options.keys())[0] # Fallback
        for label, loc_id in location_options.items():
            if loc_id == item_to_edit.locationid:
                old_location_label = label
                break

        # Bearbeitungs-Formular (Werte sind mit den alten Daten vorausgefüllt!)
        with st.form("edit_item_form"):
            st.markdown(f"**Daten für:** {item_to_edit.name}")
            
            edit_location_label = st.selectbox(
                "Lagerplatz ändern", 
                options=list(location_options.keys()),
                index=list(location_options.keys()).index(old_location_label)
            )
            
            edit_name = st.text_input("Artikelname ändern", value=item_to_edit.name)
            edit_quantity = st.number_input("Menge ändern", min_value=0.0, step=1.0, value=float(item_to_edit.quantity))
            edit_unit = st.text_input("Einheit ändern", value=item_to_edit.unit if item_to_edit.unit else "")
            edit_note = st.text_area("Notiz ändern", value=item_to_edit.note if item_to_edit.note else "", height=80)
            
            # --- NEU: Foto-Link bearbeiten (mit Fallback, falls die Eigenschaft noch leer/neu ist) ---
            current_photolink = getattr(item_to_edit, 'photolink', "") or ""
            edit_photolink = st.text_input("🔗 Dropbox Foto-Link ändern", value=current_photolink)
            
            has_expiry = item_to_edit.expirydate is not None
            edit_expiry_enabled = st.checkbox("Haltbarkeitsdatum setzen/ändern", value=has_expiry)
            edit_expirydate = None
            if edit_expiry_enabled:
                edit_expirydate = st.date_input("Neues Haltbarkeitsdatum", value=item_to_edit.expirydate if has_expiry else date.today())
            
            edit_isloanable = st.checkbox("Ausleihbar", value=item_to_edit.isloanable)
            edit_ishousehold = st.checkbox("Haushaltsartikel", value=item_to_edit.ishousehold)
            
            is_cable_old = item_to_edit.cabletype is not None or item_to_edit.cablelengthmeter is not None
            edit_is_cable = st.checkbox("Artikel ist ein Kabel", value=is_cable_old)
            
            edit_cabletype = None
            edit_cablelengthmeter = None
            if edit_is_cable:
                edit_cabletype = st.text_input("Kabeltyp", value=item_to_edit.cabletype if item_to_edit.cabletype else "")
                edit_cablelengthmeter = st.number_input(
                    "Kabellaenge in Meter", 
                    min_value=0.0, 
                    step=1.0, 
                    value=float(item_to_edit.cablelengthmeter) if item_to_edit.cablelengthmeter else 0.0
                )
            
            edit_submitted = st.form_submit_button("Änderungen speichern", type="primary", use_container_width=True)
            
            if edit_submitted:
                if not edit_name.strip():
                    st.error("Der Artikelname darf nicht leer sein.")
                else:
                    with SessionLocal() as db_session:
                        update_item(
                            session=db_session,
                            item_id=item_to_edit.id,
                            locationid=location_options[edit_location_label],
                            name=edit_name.strip(),
                            quantity=Decimal(str(edit_quantity)),
                            unit=edit_unit.strip() or None,
                            note=edit_note.strip() or None,
                            photolink=edit_photolink.strip() or None,  # --- NEU: Geänderten Link speichern ---
                            expirydate=edit_expirydate if edit_expiry_enabled else None,
                            isloanable=edit_isloanable,
                            ishousehold=edit_ishousehold,
                            cabletype=edit_cabletype.strip() if edit_cabletype and edit_is_cable else None,
                            cablelengthmeter=Decimal(str(edit_cablelengthmeter)) if edit_is_cable and edit_cablelengthmeter is not None else None,
                        )
                    st.success("Artikel erfolgreich aktualisiert!")
                    st.rerun()

        # --- LÖSCHEN-FUNKTION (Gefahrenzone) ---
        st.markdown("---")
        st.subheader("🗑️ Gefahrenzone")
        st.warning(f"Achtung: Wenn du '{item_to_edit.name}' löschst, wird der Artikel komplett aus der Datenbank entfernt.")
        
        # Eine Checkbox als Sicherung, bevor der Lösch-Button erscheint
        confirm_delete = st.checkbox("Ja, ich möchte diesen Artikel wirklich löschen.")
        
        if confirm_delete:
            if st.button("Endgültig löschen", type="primary", use_container_width=True):
                with SessionLocal() as db_session:
                    delete_item(session=db_session, item_id=item_to_edit.id)
                st.success(f"{item_to_edit.name} wurde gelöscht!")
                st.rerun()

# ==========================================
# UNTEN: BESTANDSÜBERSICHT
# ==========================================
st.divider()
st.subheader("Vorhandene Artikel")

if not items:
    st.info("Noch keine Artikel vorhanden.")
else:
    rows = [format_item_row(item) for item in items]
    
    # NEU: Falls "photolink" in deiner format_item_row auftaucht, wird es hier als klickbarer Link gerendert
    st.dataframe(
        rows, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "photolink": st.column_config.LinkColumn("📸 Foto", display_text="Anschauen 🔗")
        }
    )