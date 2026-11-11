from __future__ import annotations

from datetime import date, datetime, timezone
import enum
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class LocationType(str, enum.Enum):
    SCHRANK = "schrank"
    FACH = "fach"
    REGAL = "regal"


class SafeLocationType(TypeDecorator):
    """Mappt Datenbank-Strings fehlertolerant auf LocationType und verhindert LookupErrors."""
    impl = String(50)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if isinstance(value, LocationType):
            return value.value
        return str(value).lower().strip() if value else "fach"

    def process_result_value(self, value, dialect):
        if not value:
            return LocationType.FACH
        val = str(value).lower().strip()
        if "schrank" in val:
            return LocationType.SCHRANK
        if "regal" in val:
            return LocationType.REGAL
        return LocationType.FACH


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    passwordhash: Mapped[str] = mapped_column(String(255), nullable=False)
    createdat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    createdat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    locations: Mapped[list["Location"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint("roomid", "locationtype", "label", name="uq_location_per_room"),
        {"extend_existing": True},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    roomid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False
    )
    locationtype: Mapped[LocationType] = mapped_column(
        SafeLocationType, nullable=False, default=LocationType.FACH
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    photo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    createdat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    room: Mapped["Room"] = relationship(back_populates="locations")
    items: Mapped[list["Item"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_items_quantity_non_negative"),
        CheckConstraint(
            "cablelengthmeter IS NULL OR cablelengthmeter >= 0",
            name="ck_items_cablelength_non_negative",
        ),
        {"extend_existing": True},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    locationid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    expirydate: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_tool: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    isloanable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    isonloan: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ishousehold: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cabletype: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cablelengthmeter: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    photolink: Mapped[str | None] = mapped_column(String(500), nullable=True)
    createdat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    location: Mapped["Location"] = relationship(back_populates="items")
    loans: Mapped[list["Loan"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )
    movements: Mapped[list["StockMovement"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )


class Loan(Base):
    __tablename__ = "loans"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    itemid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    borrowername: Mapped[str] = mapped_column(String(200), nullable=False)
    loandate: Mapped[date] = mapped_column(Date, nullable=False)
    returndate: Mapped[date | None] = mapped_column(Date, nullable=True)
    isreturned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    createdat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updatedat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    item: Mapped["Item"] = relationship(back_populates="loans")


class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    itemid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    movement_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_destination: Mapped[str | None] = mapped_column(String(255), nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(255), nullable=True)
    createdat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    item: Mapped["Item"] = relationship(back_populates="movements")
