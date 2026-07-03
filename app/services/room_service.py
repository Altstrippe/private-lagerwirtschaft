from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Room


def list_rooms(session: Session) -> list[Room]:
    return list(session.scalars(select(Room).order_by(Room.name)).all())
