import streamlit as st
from app.core.config import RAEUME
from app.services import lager_service

st.set_page_config(
    page_title="Artikelverwaltung",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Artikelverwaltung")
st.caption("Erfasse neue Gegenstände, passe Mengen und Lagerorte an oder pflege technische Notizen.")

tab_anlegen, tab_bearbeiten = st.tabs([
    "➕ Neuen Artikel einsortieren",
    "✏️ Artikel bearbeiten / löschen"
])

# =============================================================
# TAB 1: NEUEN ARTIKEL EINSORTIEREN
# =============================================================
with tab_anlegen:
    st.subheader("1. Standort festlegen")
    col_r, col_t = st.columns([2, 1])
    with col_r:
        raum_neu = st.selectbox("Raum", RAEUME, key="neu_raum")
    with col_t:
        typ_neu = st.radio("Lagertyp", ["Regal", "Schrank"], horizontal=True, key="neu_typ")

    faecher_neu = lager_service.get_faecher_for_raum(raum_neu)
    col_f, col_b = st.columns([2, 1])
    with col_f:
        if faecher_neu:
            optionen = ["-- Vorhandenes Fach wählen --"] + faecher_neu + ["➕ Neues Fach / Schranknummer manuell eingeben"]
            auswahl_f = st.selectbox("Regalnummer / Fachbezeichnung *", optionen, key="neu_fach_select")
            if auswahl_f == "➕ Neues Fach / Schranknummer manuell eingeben":
                fach_neu = st.text_input("Neue Bezeichnung eingeben (z. B. Fach 11, Schrank A):", key="neu_fach_custom")
            elif auswahl_f == "-- Vorhandenes Fach wählen --":
                fach_neu = ""
            else:
                fach_neu = auswahl_f
        else:
            fach_neu = st.text_input("Regalnummer / Fachbezeichnung *", placeholder="z. B. Fach 11, Schrank A", key="neu_fach_direct")

    with col_b:
        hat_box_neu = st.checkbox("Befinden sich hier Boxen/Kisten?", key="neu_hat_box")
        box_neu = st.text_input("Kisten- / Boxen-Label:", placeholder="z. B. Box Gelb, Systainer", key="neu_box") if hat_box_neu else ""

    st.divider()

    st.subheader("2. Artikel-Eigenschaften")
    col_n, col_k = st.columns([2, 1])
    with col_n:
        name_neu = st.text_input("Bezeichnung des Artikels / Werkzeugs *", placeholder="z. B. VEVOR Zählwaage JCS-C, NYM-J 5x2.5", key="neu_name")
    with col_k:
        kat_neu = st.selectbox("Kategorie", ["Lagerwirtschaft", "Werkzeug", "Kabel"], key="neu_kat")

    # Notizfeld für Technische Daten
    notiz_neu = st.text_area(
        "📝 Notizfeld / Technische Daten (Gerätedaten, Messbereiche, Spezifikationen):",
        placeholder="z. B. 230V / 1500W, Messbereich bis 30kg, Genauigkeit 1g, Seriennummer: 4892-XYZ",
        key="neu_notiz"
    )

    menge_neu = 1.0
    einheit_neu = "Stk."
    mhd_neu = None
    kabel_typ_neu = None
    kabel_len_neu = None

    if kat_neu == "Lagerwirtschaft":
        c_m, c_e, c_mhd = st.columns([1, 1, 2])
        with c_m:
            menge_neu = st.number_input("Anfangsbestand", min_value=0.0, value=1.0, step=1.0, key="neu_m")
        with c_e:
            einheit_neu = st.selectbox("Einheit", ["Stk.", "kg", "Liter", "Meter", "Paket"], key="neu_e")
        with c_mhd:
            if st.checkbox("Mindesthaltbarkeitsdatum (MHD) erfassen?", key="neu_hat_mhd"):
                mhd_neu = st.date_input("Haltbar bis", format="DD.MM.YYYY", key="neu_mhd")

    elif kat_neu == "Werkzeug":
        c_m, c_e = st.columns([1, 1])
        with c_m:
            menge_neu = st.number_input("Menge", min_value=1.0, value=1.0, step=1.0, key="neu_m_w")
        with c_e:
            einheit_neu = st.selectbox("Einheit", ["Stk.", "Set"], key="neu_e_w")

    elif kat_neu == "Kabel":
        c_kt, c_kl = st.columns([2, 1])
        with c_kt:
            kabel_typ_neu = st.text_input("Kabeltyp", placeholder="z. B. H07RN-F 5G2.5", key="neu_k_typ")
        with c_kl:
            kabel_len_neu = st.number_input("Restlänge (in Metern)", min_value=0.0, value=50.0, step=5.0, key="neu_k_len")
        menge_neu = 1.0
        einheit_neu = "Trommel/Ring"

    col_fc, col_fl = st.columns([1, 2])
    with col_fc:
        hat_foto_neu = st.checkbox("📷 Foto vorhanden?", key="neu_hat_foto")
    with col_fl:
        foto_link_neu = st.text_input("Fotolink (URL / Google Photos):", key="neu_foto_link") if hat_foto_neu else ""

    st.divider()

    if st.button("💾 Artikel verbindlich speichern", type="primary", key="btn_save_new"):
        if not fach_neu or not fach_neu.strip():
            st.error("Bitte gib eine Fachbezeichnung an.")
        elif not name_neu or not name_neu.strip():
            st.error("Bitte gib eine Artikelbezeichnung ein.")
        else:
            try:
                lager_service.add_artikel(
                    raum=raum_neu,
                    typ=typ_neu,
                    nummer=fach_neu.strip(),
                    box=box_neu.strip(),
                    name=name_neu.strip(),
                    kategorie=kat_neu,
                    quantity=menge_neu,
                    unit=einheit_neu,
                    note=notiz_neu.strip() if notiz_neu else None,
                    cabletype=kabel_typ_neu,
                    cablelengthmeter=kabel_len_neu,
                    hat_foto=hat_foto_neu,
                    photolink=foto_link_neu,
                    expirydate=mhd_neu
                )
                st.success(f"✅ Artikel '{name_neu}' erfolgreich in Neon gespeichert!")
                st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Speichern: {e}")


# =============================================================
# TAB 2: ARTIKEL BEARBEITEN / LÖSCHEN
# =============================================================
with tab_bearbeiten:
    st.subheader("Bestehenden Artikel auswählen")

    # Alle Artikel laden
    alle_artikel = lager_service.get_all_articles_joined()

    if not alle_artikel:
        st.info("Es sind noch keine Artikel in der Datenbank vorhanden.")
    else:
        # Suchfilter über Dropdown
        artikel_dict = {
            f"{a['name']} — {a['raum']} ({a['typ']} {a['nummer']})": a['id']
            for a in alle_artikel
        }
        ausgewaehltes_label = st.selectbox(
            "Artikel suchen & auswählen:",
            options=list(artikel_dict.keys()),
            key="edit_select"
        )
        gewaehlte_id = artikel_dict[ausgewaehltes_label]

        # Frische Detaildaten abrufen
        item_data = lager_service.get_artikel_details(gewaehlte_id)

        if item_data:
            st.divider()
            st.markdown(f"### Bearbeite: **{item_data['name']}**")

            # 1. STANDORT ANPASSEN
            st.markdown("#### 1. Standort anpassen")
            col_er, col_et = st.columns([2, 1])
            with col_er:
                idx_raum = RAEUME.index(item_data['raum']) if item_data['raum'] in RAEUME else 0
                edit_raum = st.selectbox("Raum", RAEUME, index=idx_raum, key="edit_raum")
            with col_et:
                edit_typ = st.radio("Lagertyp", ["Regal", "Schrank"], index=0 if item_data['typ'] == "Fach" else 1, horizontal=True, key="edit_typ")

            col_ef, col_eb = st.columns([2, 1])
            with col_ef:
                edit_fach = st.text_input("Regalnummer / Fachbezeichnung *", value=item_data['nummer'], key="edit_fach")
            with col_eb:
                edit_box = st.text_input("Kisten- / Boxen-Label:", value=item_data['box'], key="edit_box")

            # 2. EIGENSCHAFTEN & NOTIZ ANPASSEN
            st.markdown("#### 2. Eigenschaften & Notizen")
            col_en, col_ek = st.columns([2, 1])
            with col_en:
                edit_name = st.text_input("Bezeichnung des Artikels *", value=item_data['name'], key="edit_name")
            with col_ek:
                kat_liste = ["Lagerwirtschaft", "Werkzeug", "Kabel"]
                idx_kat = kat_liste.index(item_data['kategorie']) if item_data['kategorie'] in kat_liste else 0
                edit_kat = st.selectbox("Kategorie", kat_liste, index=idx_kat, key="edit_kat")

            # Notizfeld / Technische Daten
            edit_notiz = st.text_area(
                "📝 Notizfeld / Technische Daten (z. B. Leistung, Abmessungen, Seriennummern):",
                value=item_data['note'],
                key="edit_notiz"
            )

            # Mengen & Spezifische Felder
            edit_mhd = item_data.get('expirydate')
            edit_kabel_typ = item_data.get('cabletype')
            edit_kabel_len = item_data.get('cablelengthmeter')

            col_em, col_ee = st.columns([1, 1])
            with col_em:
                edit_menge = st.number_input("Aktuelle Menge / Bestand", min_value=0.0, value=item_data['quantity'], step=1.0, key="edit_m")
            with col_ee:
                edit_einheit = st.text_input("Einheit", value=item_data['unit'], key="edit_e")

            if edit_kat == "Lagerwirtschaft":
                edit_mhd = st.date_input("Mindesthaltbarkeitsdatum (MHD)", value=item_data['expirydate'], key="edit_mhd")
            elif edit_kat == "Kabel":
                c_ekt, c_ekl = st.columns([2, 1])
                with c_ekt:
                    edit_kabel_typ = st.text_input("Kabeltyp", value=item_data['cabletype'], key="edit_kt")
                with c_ekl:
                    edit_kabel_len = st.number_input("Restlänge (Meter)", min_value=0.0, value=item_data['cablelengthmeter'], step=5.0, key="edit_kl")

            # Foto
            col_efc, col_efl = st.columns([1, 2])
            with col_efc:
                edit_hat_foto = st.checkbox("📷 Foto verknüpft?", value=item_data['hat_foto'], key="edit_hat_foto")
            with col_efl:
                edit_photolink = st.text_input("Fotolink URL:", value=item_data['photolink'], key="edit_photolink") if edit_hat_foto else ""

            st.divider()

            # AKTIONEN: SPEICHERN ODER LÖSCHEN
            col_btn_save, col_btn_del = st.columns([2, 1])

            with col_btn_save:
                if st.button("💾 Änderungen an Neon übertragen", type="primary", key="btn_update"):
                    if not edit_fach.strip() or not edit_name.strip():
                        st.error("Name und Fachnummer dürfen nicht leer sein.")
                    else:
                        success, msg = lager_service.update_artikel(
                            item_id_str=item_data['id'],
                            raum=edit_raum,
                            typ=edit_typ,
                            nummer=edit_fach.strip(),
                            box=edit_box.strip(),
                            name=edit_name.strip(),
                            kategorie=edit_kat,
                            quantity=edit_menge,
                            unit=edit_einheit.strip(),
                            note=edit_notiz.strip() if edit_notiz else None,
                            cabletype=edit_kabel_typ,
                            cablelengthmeter=edit_kabel_len,
                            expirydate=edit_mhd,
                            hat_foto=edit_hat_foto,
                            photolink=edit_photolink
                        )
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

            with col_btn_del:
                with st.expander("🗑️ Artikel löschen"):
                    st.warning("Achtung: Dies entfernt den Artikel endgültig aus der Datenbank!")
                    confirm = st.checkbox("Ja, diesen Artikel unwiderruflich löschen", key="del_confirm")
                    if st.button("Endgültig löschen", type="secondary", key="btn_del_exec"):
                        if confirm:
                            ok, del_msg = lager_service.delete_artikel(item_data['id'])
                            if ok:
                                st.success(del_msg)
                                st.rerun()
                            else:
                                st.error(del_msg)
                        else:
                            st.info("Bitte zuerst das Bestätigungs-Häkchen setzen.")
