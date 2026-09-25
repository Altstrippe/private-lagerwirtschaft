from datetime import date
import pandas as pd
import urllib.parse
from app.db.sheets_client import fetch_table, insert_row, update_cell_value

# --- HILFSFUNKTIONEN ---
def get_next_id(df: pd.DataFrame) -> int:
    if df.empty or 'ID' not in df.columns:
        return 1
    ids = pd.to_numeric(df['ID'], errors='coerce').dropna()
    return 1 if ids.empty else int(ids.max() + 1)

# --- 1. DASHBOARD-KENNZAHLEN ---
def get_dashboard_metrics() -> dict:
    df_art = fetch_table("artikel")
    df_verm = fetch_table("vermietungen")
    df_hist = fetch_table("lager_historie")
    
    gesamt_artikel = len(df_art) if not df_art.empty else 0
    
    aktive_leihe = 0
    if not df_verm.empty and "Status" in df_verm.columns:
        aktive_leihe = len(df_verm[df_verm["Status"] == "Ausgeliehen"])
        
    gesamt_bewegungen = len(df_hist) if not df_hist.empty else 0
    
    return {
        "gesamt_artikel": gesamt_artikel,
        "aktive_leihe": aktive_leihe,
        "bewegungen": gesamt_bewegungen
    }

# --- 2. LAGERPLÄTZE & FACH-INSPEKTOR ---
def get_faecher_for_raum(raum: str) -> list[str]:
    df_ort = fetch_table("orte")
    if df_ort.empty:
        return []
    return sorted(list(set(df_ort[df_ort["Raum"] == raum]["Nummer"].astype(str).tolist())))

def get_fach_inhalt(raum: str, fach_nummer: str) -> list[dict]:
    df_ort = fetch_table("orte")
    df_art = fetch_table("artikel")
    if df_ort.empty or df_art.empty:
        return []
    
    relevante_orte = df_ort[(df_ort["Raum"] == raum) & (df_ort["Nummer"].astype(str) == str(fach_nummer))]
    ort_ids = relevante_orte["ID"].tolist()
    artikel = df_art[df_art["Ort_ID"].isin(ort_ids)]
    
    items = []
    for _, art in artikel.iterrows():
        ort = relevante_orte[relevante_orte["ID"] == art["Ort_ID"]].iloc[0]
        items.append({
            "name": art["Name"],
            "kategorie": art["Kategorie"],
            "box": ort["Box"]
        })
    return items

def create_qr_link(base_url: str, raum: str, fach: str) -> str:
    params = urllib.parse.urlencode({"raum": raum, "fach": fach})
    return f"{base_url.rstrip('/')}/4_Suche/?{params}"

# --- 3. ARTIKEL ANLEGEN ---
def add_artikel(raum: str, typ: str, nummer: str, box: str, name: str, kategorie: str, hat_foto: bool) -> None:
    df_ort = fetch_table("orte")
    next_ort_id = get_next_id(df_ort)
    insert_row("orte", [next_ort_id, raum, typ, nummer, box])

    df_art = fetch_table("artikel")
    next_art_id = get_next_id(df_art)
    insert_row("artikel", [next_art_id, name, kategorie, 1 if hat_foto else 0, next_ort_id])

# --- 4. SUCHE & BESTAND ---
def get_all_articles_joined(search_term: str = None, raum_filter: str = "Alle") -> list[dict]:
    df_art = fetch_table("artikel")
    df_ort = fetch_table("orte")
    df_hist = fetch_table("lager_historie")
    df_verm = fetch_table("vermietungen")

    if df_art.empty or df_ort.empty:
        return []

    merged = pd.merge(df_art, df_ort, left_on="Ort_ID", right_on="ID", suffixes=('', '_ort'))
    
    if search_term:
        merged = merged[merged['Name'].astype(str).str.contains(search_term, case=False, na=False)]
    if raum_filter != "Alle":
        merged = merged[merged['Raum'] == raum_filter]

    results = []
    for _, row in merged.iterrows():
        a_id = row['ID']
        bestand = None
        if row['Kategorie'] == "Lagerwirtschaft" and not df_hist.empty:
            sub = df_hist[df_hist['Artikel_ID'] == a_id]
            zugang = sub[sub['Typ'] == 'Zugang']['Menge'].astype(int).sum()
            abgang = sub[sub['Typ'] == 'Abgang']['Menge'].astype(int).sum()
            bestand = zugang - abgang

        vermietung = None
        if row['Kategorie'] in ["Werkzeug", "Kabel"] and not df_verm.empty:
            v_akt = df_verm[(df_verm['Artikel_ID'] == a_id) & (df_verm['Status'] == 'Ausgeliehen')]
            if not v_akt.empty:
                vermietung = f"Vermietet an {v_akt.iloc[0]['Person']} seit {v_akt.iloc[0]['Datum_Ausgabe']}"

        results.append({
            "id": a_id,
            "name": row['Name'],
            "kategorie": row['Kategorie'],
            "raum": row['Raum'],
            "typ": row['Typ'],
            "nummer": row['Nummer'],
            "box": row['Box'],
            "hat_foto": bool(row['Hat_Foto']),
            "bestand": bestand,
            "vermietung": vermietung
        })
    return results

# --- 5. LAGERWIRTSCHAFT (ZU- / ABGANG) ---
def get_lagerwirtschaft_artikel() -> dict[str, int]:
    df_art = fetch_table("artikel")
    if df_art.empty:
        return {}
    sub = df_art[df_art["Kategorie"] == "Lagerwirtschaft"]
    return {row["Name"]: row["ID"] for _, row in sub.iterrows()}

def buche_lagerbewegung(artikel_id: int, bewegungstyp: str, menge: int, buchungsdatum: date) -> None:
    df_hist = fetch_table("lager_historie")
    next_id = get_next_id(df_hist)
    insert_row("lager_historie", [next_id, artikel_id, bewegungstyp, int(menge), str(buchungsdatum)])

# --- 6. AUSLEIHE & VERMIETUNG ---
def get_leihbare_artikel() -> dict[str, int]:
    df_art = fetch_table("artikel")
    if df_art.empty:
        return {}
    sub = df_art[df_art["Kategorie"].isin(["Werkzeug", "Kabel"])]
    return {row["Name"]: row["ID"] for _, row in sub.iterrows()}

def leihe_artikel_aus(artikel_id: int, person: str, ausgabedatum: date) -> tuple[bool, str]:
    df_verm = fetch_table("vermietungen")
    if not df_verm.empty:
        schon_verliehen = not df_verm[(df_verm['Artikel_ID'] == artikel_id) & (df_verm['Status'] == 'Ausgeliehen')].empty
        if schon_verliehen:
            return False, "Dieser Artikel ist laut System bereits verliehen!"
            
    next_id = get_next_id(df_verm)
    insert_row("vermietungen", [next_id, artikel_id, person, str(ausgabedatum), "", "Ausgeliehen"])
    return True, f"Erfolgreich an {person} ausgegeben."

def get_aktive_ausleihen() -> list[dict]:
    df_verm = fetch_table("vermietungen")
    df_art = fetch_table("artikel")
    if df_verm.empty or df_art.empty:
        return []
    
    offene = df_verm[df_verm['Status'] == 'Ausgeliehen']
    if offene.empty:
        return []
        
    merged = pd.merge(offene, df_art, left_on="Artikel_ID", right_on="ID", suffixes=('_v', '_a'))
    return [
        {
            "id": row["ID_v"],
            "name": row["Name"],
            "person": row["Person"],
            "datum_ausgabe": row["Datum_Ausgabe"]
        }
        for _, row in merged.iterrows()
    ]

def nimm_artikel_zurueck(vermietung_id: int, rueckgabedatum: date) -> None:
    df_verm = fetch_table("vermietungen")
    row_idx = df_verm[df_verm['ID'] == vermietung_id].index[0] + 2
    update_cell_value("vermietungen", row_idx, 5, str(rueckgabedatum))
    update_cell_value("vermietungen", row_idx, 6, "Zurückgegeben")
