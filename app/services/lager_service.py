from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from typing import Generator
import urllib.parse
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Item, Loan, Location, LocationType, Room
from app.db.session import SessionLocal


# --- SESSION HELFER ---
@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Kontext-Manager für sichere Transaktionen."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# --- 1. DASHBOARD-KENNZAHLEN ---
def get_dashboard_metrics() -> dict:
    with get_db_session() as db:
        gesamt_artikel = db.scalar(select(func.count(Item.id))) or 0
        aktive_leihe = (
            db.scalar(select(func.count(Loan.id)).where(Loan.isreturned.is_(False)))
            or 0
        )
        gesamt_orte = db.scalar(select(func.count(Location.id))) or 0

        return {
            "gesamt_artikel": int(gesamt_artikel),
            "aktive_leihe": int(aktive_leihe),
            "gesamt_orte": int(gesamt_orte),
        }


# --- 2. RÄUME & STELLPLÄTZE ---
def ensure_default_rooms(room_names: list[str]) -> None:
    """Stellt sicher, dass die Standardräume in der Datenbank existieren."""
    with get_db_session() as db:
        for name in room_names:
            stmt = select(Room).where(Room.name == name)
            if not db.scalar(stmt):
                db.add(Room(name=name))


def add_location(
    room_name: str,
    label: str,
    location_type: str = "fach",
    note: str | None = None,
) -> tuple[bool, str]:
    """Legt ein neues Fach oder einen Schrank direkt in Neon PostgreSQL an."""
    if not label or not label.strip():
        return False, "Bitte eine Fach- oder Schrankbezeichnung eingeben."

    clean_label = label.strip()
    with get_db_session() as db:
        room = db.scalar(select(Room).where(Room.name == room_name))
        if not room:
            room = Room(name=room_name)
            db.add(room)
            db.flush()

        loc_enum = (
            LocationType.FACH
            if location_type.lower() == "fach"
            else LocationType.SCHRANK
        )

        existing = db.scalar(
            select(Location).where(
                Location.roomid == room.id,
                Location.locationtype == loc_enum,
                Location.label == clean_label,
            )
        )
        if existing:
            return (
                False,
                f"Das {loc_enum.value.capitalize()} '{clean_label}' existiert im Raum '{room_name}' bereits.",
            )

        new_loc = Location(
            roomid=room.id,
            locationtype=loc_enum,
            label=clean_label,
            note=note.strip() if note else None,
        )
        db.add(new_loc)
        return (
            True,
            f"{loc_enum.value.capitalize()} '{clean_label}' erfolgreich im Raum '{room_name}' gespeichert!",
        )


def get_faecher_for_raum(room_name: str) -> list[str]:
    """Liefert alle Fach- und Schranknummern für einen Raum zurück."""
    with get_db_session() as db:
        stmt = (
            select(Location.label)
            .join(Room)
            .where(Room.name == room_name)
            .order_by(Location.label)
        )
        return list(db.scalars(stmt).all())


def get_fach_inhalt(room_name: str, label: str) -> list[dict]:
    """Ermittelt den exakten Inhalt für Fach-Inspektor und QR-Scan."""
    with get_db_session() as db:
        stmt = (
            select(Item)
            .join(Location)
            .join(Room)
            .where(Room.name == room_name, Location.label == label)
            .options(joinedload(Item.location))
        )
        items = db.scalars(stmt).all()

        results = []
        for it in items:
            box_info = it.location.note if it.location and it.location.note else ""
            kategorie = (
                "Werkzeug"
                if it.is_tool
                else ("Kabel" if it.cabletype else "Lagerwirtschaft")
            )
            results.append(
                {
                    "id": str(it.id),
                    "name": it.name,
                    "quantity": float(it.quantity),
                    "unit": it.unit or "Stk.",
                    "kategorie": kategorie,
                    "box": box_info,
                    "isonloan": it.isonloan,
                    "photolink": it.photolink,
                }
            )
        return results


def create_qr_link(base_url: str, raum: str, fach: str) -> str:
    """Erzeugt den Tiefenlink für Regalschilder."""
    params = urllib.parse.urlencode({"raum": raum, "fach": fach})
    return f"{base_url.rstrip('/')}/4_Suche/?{params}"


# --- 3. ARTIKEL ANLEGEN, BEARBEITEN & LÖSCHEN ---
def add_artikel(
    raum: str,
    typ: str,
    nummer: str,
    box: str,
    name: str,
    kategorie: str,
    quantity: float = 0.0,
    unit: str = "Stk.",
    note: str | None = None,
    cabletype: str | None = None,
    cablelengthmeter: float | None = None,
    hat_foto: bool = False,
    photolink: str | None = None,
    expirydate: date | None = None,
) -> None:
    with get_db_session() as db:
        room = db.scalar(select(Room).where(Room.name == raum))
        if not room:
            room = Room(name=raum)
            db.add(room)
            db.flush()

        loc_enum = (
            LocationType.FACH if typ.lower() in ["regal", "fach"] else LocationType.SCHRANK
        )
        loc = db.scalar(
            select(Location).where(
                Location.roomid == room.id,
                Location.locationtype == loc_enum,
                Location.label == nummer.strip(),
            )
        )

        if not loc:
            loc = Location(
                roomid=room.id,
                locationtype=loc_enum,
                label=nummer.strip(),
                note=box.strip() if box else None,
            )
            db.add(loc)
            db.flush()
        elif box and not loc.note:
            loc.note = box.strip()

        is_tool = kategorie == "Werkzeug"
        is_loanable = kategorie in ["Werkzeug", "Kabel"]
        photo_val = (
            photolink.strip()
            if (hat_foto and photolink and photolink.strip())
            else ("vorhanden" if hat_foto else None)
        )

        new_item = Item(
            locationid=loc.id,
            name=name.strip(),
            quantity=quantity,
            unit=unit.strip() if unit else "Stk.",
            note=note.strip() if note else None,
            ishousehold=False,
            is_tool=is_tool,
            isloanable=is_loanable,
            cabletype=cabletype.strip() if (kategorie == "Kabel" and cabletype) else None,
            cablelengthmeter=cablelengthmeter if kategorie == "Kabel" else None,
            expirydate=expirydate if kategorie == "Lagerwirtschaft" else None,
            photolink=photo_val,
        )
        db.add(new_item)


def get_artikel_details(item_id_str: str) -> dict | None:
    """Holt die vollständigen Detaildaten eines Artikels zur Bearbeitung."""
    with get_db_session() as db:
        item = db.get(
            Item,
            uuid.UUID(item_id_str),
            options=[joinedload(Item.location).joinedload(Location.room)],
        )
        if not item:
            return None

        loc = item.location
        return {
            "id": str(item.id),
            "name": item.name,
            "raum": loc.room.name if loc and loc.room else "Halle",
            "typ": loc.locationtype.value.capitalize() if loc else "Fach",
            "nummer": loc.label if loc else "",
            "box": loc.note if loc and loc.note else "",
            "kategorie": (
                "Werkzeug"
                if item.is_tool
                else ("Kabel" if item.cabletype else "Lagerwirtschaft")
            ),
            "quantity": float(item.quantity),
            "unit": item.unit or "Stk.",
            "note": item.note or "",
            "expirydate": item.expirydate,
            "cabletype": item.cabletype or "",
            "cablelengthmeter": float(item.cablelengthmeter) if item.cablelengthmeter else 0.0,
            "photolink": item.photolink or "",
            "hat_foto": bool(item.photolink),
            "isonloan": item.isonloan,
        }


def update_artikel(
    item_id_str: str,
    raum: str,
    typ: str,
    nummer: str,
    box: str,
    name: str,
    kategorie: str,
    quantity: float,
    unit: str,
    note: str | None = None,
    cabletype: str | None = None,
    cablelengthmeter: float | None = None,
    expirydate: date | None = None,
    hat_foto: bool = False,
    photolink: str | None = None,
) -> tuple[bool, str]:
    """Aktualisiert alle Eigenschaften, Mengen oder versetzt den Artikel in ein anderes Fach."""
    with get_db_session() as db:
        item = db.get(Item, uuid.UUID(item_id_str))
        if not item:
            return False, "Artikel nicht gefunden."

        room = db.scalar(select(Room).where(Room.name == raum))
        if not room:
            room = Room(name=raum)
            db.add(room)
            db.flush()

        loc_enum = (
            LocationType.FACH if typ.lower() in ["regal", "fach"] else LocationType.SCHRANK
        )
        loc = db.scalar(
            select(Location).where(
                Location.roomid == room.id,
                Location.locationtype == loc_enum,
                Location.label == nummer.strip(),
            )
        )
        if not loc:
            loc = Location(
                roomid=room.id,
                locationtype=loc_enum,
                label=nummer.strip(),
                note=box.strip() if box else None,
            )
            db.add(loc)
            db.flush()
        elif box:
            loc.note = box.strip()

        is_tool = kategorie == "Werkzeug"
        is_loanable = kategorie in ["Werkzeug", "Kabel"]
        photo_val = (
            photolink.strip()
            if (hat_foto and photolink and photolink.strip())
            else ("vorhanden" if hat_foto else None)
        )

        item.locationid = loc.id
        item.name = name.strip()
        item.quantity = quantity
        item.unit = unit.strip() if unit else "Stk."
        item.note = note.strip() if note else None
        item.is_tool = is_tool
        item.isloanable = is_loanable
        item.cabletype = cabletype.strip() if (kategorie == "Kabel" and cabletype) else None
        item.cablelengthmeter = cablelengthmeter if kategorie == "Kabel" else None
        item.expirydate = expirydate if kategorie == "Lagerwirtschaft" else None
        item.photolink = photo_val

        return True, f"Artikel '{item.name}' erfolgreich aktualisiert!"


def delete_artikel(item_id_str: str) -> tuple[bool, str]:
    """Löscht einen Artikel sicher aus Neon PostgreSQL."""
    with get_db_session() as db:
        item = db.get(Item, uuid.UUID(item_id_str))
        if not item:
            return False, "Artikel nicht gefunden."

        if item.isonloan:
            return (
                False,
                f"Artikel '{item.name}' ist aktuell verliehen und kann erst nach Rückgabe gelöscht werden!",
            )

        name = item.name
        db.delete(item)
        return True, f"Artikel '{name}' wurde erfolgreich gelöscht."

# --- 4. SUCHE ÜBER ALLES ---
def get_all_articles_joined(
    search_term: str | None = None, raum_filter: str = "Alle"
) -> list[dict]:
    with get_db_session() as db:
        stmt = (
            select(Item)
            .join(Location)
            .join(Room)
            .options(joinedload(Item.location).joinedload(Location.room))
        )

        if search_term:
            stmt = stmt.where(
                or_(
                    Item.name.ilike(f"%{search_term}%"),
                    Location.label.ilike(f"%{search_term}%"),
                    Item.cabletype.ilike(f"%{search_term}%"),
                )
            )

        if raum_filter != "Alle":
            stmt = stmt.where(Room.name == raum_filter)

        items = db.scalars(stmt).all()

        results = []
        for it in items:
            loc = it.location
            room_name = loc.room.name if loc and loc.room else "Unbekannt"
            loc_label = loc.label if loc else "-"
            loc_typ = loc.locationtype.value.capitalize() if loc else "-"
            box = loc.note if loc and loc.note else ""

            kategorie = (
                "Werkzeug"
                if it.is_tool
                else ("Kabel" if it.cabletype else "Lagerwirtschaft")
            )

            verleih_info = None
            if it.isonloan:
                loan_stmt = (
                    select(Loan)
                    .where(Loan.itemid == it.id, Loan.isreturned.is_(False))
                    .order_by(Loan.createdat.desc())
                )
                akt_loan = db.scalar(loan_stmt)
                if akt_loan:
                    verleih_info = f"Vermietet an {akt_loan.borrowername} seit {akt_loan.loandate.strftime('%d.%m.%Y')}"

            results.append(
                {
                    "id": str(it.id),
                    "name": it.name,
                    "kategorie": kategorie,
                    "raum": room_name,
                    "typ": loc_typ,
                    "nummer": loc_label,
                    "box": box,
                    "quantity": float(it.quantity),
                    "bestand": float(it.quantity),
                    "unit": it.unit or "Stk.",
                    "hat_foto": bool(it.photolink),
                    "photolink": it.photolink,
                    "isonloan": it.isonloan,
                    "vermietung": verleih_info,
                }
            )
        return results


# --- 5. LAGERWIRTSCHAFT (BESTAND ZU- / ABGANG) ---
def get_lagerwirtschaft_artikel() -> list[dict]:
    with get_db_session() as db:
        stmt = (
            select(Item)
            .where(Item.is_tool.is_(False), Item.cabletype.is_(None))
            .order_by(Item.name)
        )
        items = db.scalars(stmt).all()
        return [
            {
                "id": str(it.id),
                "name": it.name,
                "quantity": float(it.quantity),
                "unit": it.unit or "Stk.",
            }
            for it in items
        ]


def buche_lagerbewegung(
    item_id_str: str, typ: str, menge: float, datum: date
) -> float:
    with get_db_session() as db:
        item = db.get(Item, uuid.UUID(item_id_str))
        if not item:
            raise ValueError("Artikel nicht gefunden.")

        aktuelle_menge = float(item.quantity)
        if typ == "Zugang":
            neue_menge = aktuelle_menge + menge
        else:
            if aktuelle_menge < menge:
                raise ValueError(
                    f"Nicht genügend Bestand! Vorhanden: {aktuelle_menge}"
                )
            neue_menge = aktuelle_menge - menge

        item.quantity = neue_menge
        return neue_menge


# --- 6. AUSLEIHE & VERMIETUNG (WERKZEUG / KABEL) ---
def get_leihbare_artikel() -> list[dict]:
    with get_db_session() as db:
        stmt = (
            select(Item)
            .where(or_(Item.is_tool.is_(True), Item.isloanable.is_(True)))
            .order_by(Item.name)
        )
        items = db.scalars(stmt).all()
        return [
            {
                "id": str(it.id),
                "name": it.name,
                "isonloan": it.isonloan,
                "kategorie": "Werkzeug" if it.is_tool else "Kabel",
            }
            for it in items
        ]


def leihe_artikel_aus(
    item_id_str: str, person: str, ausgabedatum: date
) -> tuple[bool, str]:
    with get_db_session() as db:
        item = db.get(Item, uuid.UUID(item_id_str))
        if not item:
            return False, "Artikel nicht gefunden."

        if item.isonloan:
            return False, f"'{item.name}' ist aktuell bereits ausgeliehen!"

        new_loan = Loan(
            itemid=item.id,
            borrowername=person.strip(),
            loandate=ausgabedatum,
            isreturned=False,
        )
        item.isonloan = True
        db.add(new_loan)
        return True, f"'{item.name}' erfolgreich an {person} ausgegeben."


def get_aktive_ausleihen() -> list[dict]:
    with get_db_session() as db:
        stmt = (
            select(Loan)
            .where(Loan.isreturned.is_(False))
            .options(joinedload(Loan.item))
            .order_by(Loan.loandate.desc())
        )
        loans = db.scalars(stmt).all()
        return [
            {
                "loan_id": str(lo.id),
                "item_name": lo.item.name if lo.item else "Unbekannt",
                "person": lo.borrowername,
                "datum_ausgabe": lo.loandate.strftime("%d.%m.%Y"),
            }
            for lo in loans
        ]


def nimm_artikel_zurueck(loan_id_str: str, rueckgabedatum: date) -> str:
    with get_db_session() as db:
        loan = db.get(Loan, uuid.UUID(loan_id_str))
        if not loan:
            raise ValueError("Ausleihvorgang nicht gefunden.")

        loan.returndate = rueckgabedatum
        loan.isreturned = True

        if loan.item:
            loan.item.isonloan = False
            item_name = loan.item.name
        else:
            item_name = "Artikel"

        return f"'{item_name}' wurde erfolgreich zurückgebucht."
