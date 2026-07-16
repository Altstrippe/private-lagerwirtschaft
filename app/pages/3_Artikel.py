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
        
        photolink = st.text_input("🔗 Dropbox Foto-Link (Optional)", placeholder="https://www.dropbox.com/...")

        expiry_enabled = st.checkbox("Haltbarkeitsdatum setzen")
        expirydate = None
        if expiry_enabled:
            expirydate = st.date_input("Haltbarkeitsdatum", value=date.today())

        st.markdown("---")
        st.write("**Eigenschaften**")
        col_prop1, col_prop2 = st.columns(2)
        
        with col_prop1:
            isloanable = st.checkbox("Ausleihbar")
            ishousehold = st.checkbox("Haushaltsartikel")
            is_tool = st.checkbox("Werkzeug") # <--- NEU: Werkzeug Haken
            
        with col_prop2:
            # Kabel-Felder sind jetzt immer sichtbar
            cabletype = st.text_input("Kabeltyp (Optional)", placeholder="z.B. CAT7, H07RN-F")
            cablelengthmeter = st.number_input(
                "Kabellaenge in Meter (Optional)",
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
                        photolink=photolink.strip() or None,  
                        expirydate=expirydate if expiry_enabled else None,
                        isloanable=isloanable,
                        ishousehold=ishousehold,
                        is_tool=is_tool, # <--- NEU
                        cabletype=cabletype.strip() if cabletype else None,
                        cablelengthmeter=Decimal(str(cablelengthmeter)) if cablelengthmeter > 0 else None,
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
        
        selected_item_label = st.selectbox("Welchen Artikel möchtest du bearbeiten?", options=list(item_options.keys()))
        item_to_edit = item_options[selected_item_label]
        
        # Herausfinden, welcher Lagerplatz-Text dem aktuell hinterlegten Ort entspricht
        old_location_label = list(location_options.keys())[0] # Fallback
        for label, loc_id in location_options.items():
            if loc_id == item_to_edit.locationid:
                old_location_label = label
                break

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
            
            current_photolink = getattr(item_to_edit, 'photolink', "") or ""
            edit_photolink = st.text_input("🔗 Dropbox Foto-Link ändern", value=current_photolink)
            
            has_expiry = item_to_edit.expirydate is not None
            edit_expiry_enabled = st.checkbox("Haltbarkeitsdatum setzen/ändern", value=has_expiry)
            edit_expirydate = None
            if edit_expiry_enabled:
                edit_expirydate = st.date_input("Neues Haltbarkeitsdatum", value=item_to_edit.expirydate if has_expiry else date.today())
            
            st.markdown("---")
            st.write("**Eigenschaften ändern**")
            edit_col_prop1, edit_col_prop2 = st.columns(2)
            
            with edit_col_prop1:
                edit_isloanable = st.checkbox("Ausleihbar", value=item_to_edit.isloanable)
                edit_ishousehold = st.checkbox("Haushaltsartikel", value=item_to_edit.ishousehold)
                # Fallback für den Boolean-Wert, falls das Feld im alten Objekt nicht existiert
                current_is_tool = getattr(item_to_edit, 'is_tool', False)
                edit_is_tool = st.checkbox("Werkzeug", value=current_is_tool)
                
            with edit_col_prop2:
                # Kabel-Felder sind jetzt immer sichtbar
                edit_cabletype = st.text_input("Kabeltyp (Optional)", value=item_to_edit.cabletype if item_to_edit.cabletype else "")
                edit_cablelengthmeter = st.number_input(
                    "Kabellaenge in Meter (Optional)", 
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
                            photolink=edit_photolink.strip() or None, 
                            expirydate=edit_expirydate if edit_expiry_enabled else None,
                            isloanable=edit_isloanable,
                            ishousehold=edit_ishousehold,
                            is_tool=edit_is_tool, # <--- NEU
                            cabletype=edit_cabletype.strip() if edit_cabletype else None,
                            cablelengthmeter=Decimal(str(edit_cablelengthmeter)) if edit_cablelengthmeter > 0 else None,
                        )
                    st.success("Artikel erfolgreich aktualisiert!")
                    st.rerun()

        # --- LÖSCHEN-FUNKTION (Gefahrenzone) ---
        st.markdown("---")
        st.subheader("🗑️ Gefahrenzone")
        st.warning(f"Achtung: Wenn du '{item_to_edit.name}' löschst, wird der Artikel komplett aus der Datenbank entfernt.")
        
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
    
    # HIER IST DIE ÄNDERUNG: Tabelle klickbar machen und ID verstecken
    selection = st.dataframe(
        rows, 
        use_container_width=True, 
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",           
        column_config={
            "ID": None,              
            "photolink": st.column_config.LinkColumn("📸 Foto", display_text="Anschauen 🔗")
        }
    )

    # WENN EINE ZEILE ANGEKLICKT WIRD, DETAILS ANZEIGEN:
    if len(selection.selection.rows) > 0:
        selected_index = selection.selection.rows[0]
        selected_item = items[selected_index]

        st.markdown("---")
        st.subheader(f"🏷️ Details: {selected_item.name}")
        
        detail_col1, detail_col2 = st.columns(2)
        with detail_col1:
            st.markdown(f"**Lagerort:** {selected_item.location.room.name} | {selected_item.location.locationtype.value} | {selected_item.location.label}")
            st.markdown(f"**Menge:** {float(selected_item.quantity)} {selected_item.unit or ''}")
            if selected_item.expirydate:
                st.markdown(f"**Haltbarkeit:** {selected_item.expirydate.isoformat()}")
            if selected_item.note:
                st.info(f"**Notiz:** {selected_item.note}")

        with detail_col2:
            st.markdown(f"**Werkzeug:** {'Ja' if selected_item.is_tool else 'Nein'}")
            st.markdown(f"**Haushalt:** {'Ja' if selected_item.ishousehold else 'Nein'}")
            st.markdown(f"**Ausleihbar:** {'Ja' if selected_item.isloanable else 'Nein'}")
            st.markdown(f"**Ausgeliehen:** {'Ja' if selected_item.isonloan else 'Nein'}")
            
            if selected_item.cabletype or selected_item.cablelengthmeter:
                st.markdown(f"**Kabel:** {selected_item.cabletype or '-'} ({float(selected_item.cablelengthmeter) if selected_item.cablelengthmeter else 0} m)")
            
            if selected_item.photolink:
                st.markdown(f"[📸 Foto in Dropbox öffnen]({selected_item.photolink})")