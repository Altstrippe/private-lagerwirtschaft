from __future__ import annotations

from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text

from app.db.models import Item, Location, Room


def create_item(
    session: Session,
    locationid: int,
    name: str,
    quantity,
    unit: str | None = None,
    note: str | None = None,
    expirydate=None,
    isloanable: bool = False,
    ishousehold: bool = False,
    is_tool: bool = False,  # <--- NEU: Werkzeug
    cabletype: str | None = None,
    cablelengthmeter=None,
    photolink: str | None = None,
):
    
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Der Artikelname darf nicht leer sein.")

    # Neues Item erstellen
    item = Item(
        locationid=locationid,
        name=clean_name,
        quantity=quantity,
        unit=unit.strip() if unit else None,
        note=note.strip() if note else None,
        expirydate=expirydate,
        isloanable=isloanable,
        ishousehold=ishousehold,
        is_tool=is_tool,  # <--- NEU: Werkzeug
        cabletype=cabletype.strip() if cabletype else None,
        cablelengthmeter=cablelengthmeter,
        photolink=photolink,
    )
    
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def list_items(session: Session) -> list[Item]:
    stmt = (
        select(Item)
        .options(joinedload(Item.location).joinedload(Location.room))
        .order_by(Item.name)
    )
    return list(session.scalars(stmt).all())


def search_items(session: Session, query: str) -> list[Item]:
    clean_query = query.strip()
    if not clean_query:
        return []

    like = f"%{clean_query}%"

    stmt = (
        select(Item)
        .join(Item.location)
        .join(Location.room)
        .options(joinedload(Item.location).joinedload(Location.room))
        .where(
            or_(
                Item.name.ilike(like),
                Item.note.ilike(like),
                Item.cabletype.ilike(like),
                Location.label.ilike(like),
                Room.name.ilike(like),
            )
        )
        .order_by(Room.name, Location.label, Item.name)
    )
    return list(session.scalars(stmt).all())


def list_stock_items(
    session: Session,
    room_name: str | None = None,
    only_loanable: bool = False,
    only_on_loan: bool = False,
    only_with_expiry: bool = False,
    only_household: bool = False,
    only_cables: bool = False,
    only_tools: bool = False,  # <--- NEU: Filter für Werkzeuge
) -> list[Item]:
    stmt = (
        select(Item)
        .join(Item.location)
        .join(Location.room)
        .options(joinedload(Item.location).joinedload(Location.room))
    )

    if room_name and room_name != "Alle":
        stmt = stmt.where(Room.name == room_name)

    if only_loanable:
        stmt = stmt.where(Item.isloanable.is_(True))

    if only_on_loan:
        stmt = stmt.where(Item.isonloan.is_(True))

    if only_with_expiry:
        stmt = stmt.where(Item.expirydate.is_not(None))

    if only_household:
        stmt = stmt.where(Item.ishousehold.is_(True))

    if only_tools:  # <--- NEU: Filter für Werkzeuge
        stmt = stmt.where(Item.is_tool.is_(True))

    if only_cables:
        stmt = stmt.where(
            (Item.cabletype.is_not(None)) | (Item.cablelengthmeter.is_not(None))
        )

    stmt = stmt.order_by(Room.name, Location.locationtype, Location.label, Item.name)

    return list(session.scalars(stmt).all())


def delete_item(session: Session, item_id) -> bool:
    """Löscht einen Artikel inkl. seiner Ausleih-Historie komplett aus der Datenbank."""
    item = session.get(Item, item_id)
    if item:
        # 1. Zuerst alle verknüpften Ausleih-Einträge (loans) löschen
        session.execute(text("DELETE FROM loans WHERE itemid = :id"), {"id": item_id})
        
        # 2. Dann den Artikel selbst löschen
        session.delete(item)
        session.commit()
        return True
    return False


def list_loanable_available_items(session: Session) -> list[Item]:
    stmt = (
        select(Item)
        .options(joinedload(Item.location).joinedload(Location.room))
        .where(
            Item.isloanable.is_(True),
            Item.isonloan.is_(False),
        )
        .order_by(Item.name)
    )
    return list(session.scalars(stmt).all())


def update_item(
    session: Session,
    item_id: int,
    locationid: int,
    name: str,
    quantity: Decimal,
    unit: str | None = None,
    note: str | None = None,
    expirydate=None,
    isloanable: bool = False,
    ishousehold: bool = False,
    is_tool: bool = False,  # <--- NEU: Werkzeug
    cabletype: str | None = None,
    cablelengthmeter=None,
    photolink: str | None = None,
) -> Item:
    # 1. Artikel anhand seiner ID aus der Datenbank holen
    item = session.get(Item, item_id)
    if not item:
        raise ValueError("Artikel wurde nicht gefunden.")

    # 2. Name bereinigen und validieren
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Der Artikelname darf nicht leer sein.")

    # 3. Die neuen Werte übergeben
    item.locationid = locationid
    item.name = clean_name
    item.quantity = quantity
    item.unit = unit.strip() if unit else None
    item.note = note.strip() if note else None
    item.expirydate = expirydate
    item.isloanable = isloanable
    item.ishousehold = ishousehold
    item.is_tool = is_tool  # <--- NEU: Werkzeug
    item.cabletype = cabletype.strip() if cabletype else None
    item.cablelengthmeter = cablelengthmeter
    item.photolink = photolink

    # 4. In die Datenbank speichern
    session.commit()
    session.refresh(item)
    return item