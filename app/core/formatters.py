from __future__ import annotations

from app.db.models import Item


def format_item_row(item: Item) -> dict[str, object]:
    return {
        "ID": str(item.id),  # <--- NEU: Wichtig für die klickbare Tabelle gleich!
        "Artikel": item.name,
        "Menge": float(item.quantity),
        "Einheit": item.unit or "",
        "Raum": item.location.room.name,
        "Typ": item.location.locationtype.value,
        "Nummer": item.location.label,
        "Werkzeug": "Ja" if item.is_tool else "Nein",  # <--- NEU: Werkzeug-Markierung
        "Ausleihbar": "Ja" if item.isloanable else "Nein",
        "Ausgeliehen": "Ja" if item.isonloan else "Nein",
        "Haushalt": "Ja" if item.ishousehold else "Nein",
        "Haltbarkeit": item.expirydate.isoformat() if item.expirydate else "",
        "Kabeltyp": item.cabletype or "",
        "Meter": float(item.cablelengthmeter) if item.cablelengthmeter else "",
        "Notiz": item.note or "",
        "photolink": item.photolink,
    }