from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models import Room, User

DEFAULT_ROOMS = [
    "Halle",
    "Werkstatt",
    "EVA",
    "Honigraum",
]


def seed_rooms(session: Session) -> None:
    existing_names = set(session.scalars(select(Room.name)).all())

    for room_name in DEFAULT_ROOMS:
        if room_name not in existing_names:
            session.add(Room(name=room_name))

    session.commit()


def seed_user(session: Session) -> None:
    settings = get_settings()

    existing_user = session.scalar(
        select(User).where(User.username == settings.app_username)
    )
    if existing_user:
        return

    user = User(
        username=settings.app_username,
        passwordhash=hash_password(settings.app_password),
    )
    session.add(user)
    session.commit()


def run_seed(session: Session) -> None:
    seed_rooms(session)
    seed_user(session)