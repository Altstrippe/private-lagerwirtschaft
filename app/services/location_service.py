from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Location, LocationType, Room


def list_locations(session: Session) -> list[Location]:
    stmt = (
        select(Location)
        .join(Location.room)
        .options(joinedload(Location.room))
        .order_by(Room.name, Location.locationtype, Location.label)
    )
    return list(session.scalars(stmt).all())


def create_location(
    session: Session,
    roomid,
    locationtype: LocationType,
    label: str,
    note: str | None = None,
    photo_path: str | None = None,
) -> Location:
    clean_label = label.strip()

    if not clean_label:
        raise ValueError("Schranknummer oder Fachnummer ist erforderlich.")

    existing = session.scalar(
        select(Location).where(
            Location.roomid == roomid,
            Location.locationtype == locationtype,
            Location.label == clean_label,
        )
    )
    if existing:
        raise ValueError("Dieser Lagerplatz existiert bereits.")

    location = Location(
        roomid=roomid,
        locationtype=locationtype,
        label=clean_label,
        note=note.strip() if note else None,
        photo_path=photo_path,
    )
    session.add(location)
    session.commit()
    session.refresh(location)
    return location
