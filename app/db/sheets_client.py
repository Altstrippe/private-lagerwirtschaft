import pandas as pd
from app.core.config import get_spreadsheet

spreadsheet = get_spreadsheet()

def fetch_table(tab_name: str) -> pd.DataFrame:
    """Liest ein komplettes Tabellenblatt als DataFrame."""
    ws = spreadsheet.worksheet(tab_name)
    data = ws.get_all_records()
    return pd.DataFrame(data)

def insert_row(tab_name: str, values: list) -> None:
    """Hängt eine neue Zeile an das angegebene Tabellenblatt an."""
    ws = spreadsheet.worksheet(tab_name)
    ws.append_row(values)

def update_cell_value(tab_name: str, row_idx: int, col_idx: int, value: str) -> None:
    """Aktualisiert eine einzelne Zelle gezielt (1-basierter Index)."""
    ws = spreadsheet.worksheet(tab_name)
    ws.update_cell(row_idx, col_idx, value)
