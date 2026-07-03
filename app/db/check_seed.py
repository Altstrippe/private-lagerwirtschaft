from sqlalchemy import select

from app.db.models import Room, User
from app.db.session import SessionLocal


def main() -> None:
    with SessionLocal() as session:
        rooms = session.scalars(select(Room.name).order_by(Room.name)).all()
        users = session.scalars(select(User.username).order_by(User.username)).all()

    print("Räume:", rooms)
    print("Benutzer:", users)


if __name__ == "__main__":
    main()