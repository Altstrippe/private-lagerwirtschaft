from __future__ import annotations

from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Item, Location, Room


def create_item(
    session: Session,
    locationid,
    name: str,
    quantity: Decimal,
    unit: str | None = None,
    note: str | None = None,
    expirydate=None,
    isloanable: bool = False,
    cabletype: str | None = None,
    cablelengthmeter: Decimal | None = None,
) -> Item:
    clean_name = name.strip()

    if not clean_name:
        raise ValueError("Artikelname ist erforderlich.")

    if quantity < Decimal("0"):
        raise ValueError("Menge darf nicht negativ sein.")

    if cablelengthmeter is not None and cablelengthmeter < Decimal("0"):
        raise ValueError("Kabellaenge darf nicht negativ sein.")

    item = Item(
        locationid=locationid,
        name=clean_name,
        quantity=quantity,
        unit=unit.strip() if unit else None,
        note=note.strip() if note else None,
        expirydate=expirydate,
        isloanable=isloanable,
        cabletype=cabletype.strip() if cabletype else None,
        cablelengthmeter=cablelengthmeter,
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

    stmt = stmt.order_by(Room.name, Location.locationtype, Location.label, Item.name)

    return list(session.scalars(stmt).all())

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
