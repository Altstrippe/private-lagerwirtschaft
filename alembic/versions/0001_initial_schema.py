"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


locationtype_enum = postgresql.ENUM(
    "schrank",
    "fach",
    name="locationtype_enum",
    create_type=False,
)

def upgrade() -> None:
    locationtype_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("passwordhash", sa.String(length=255), nullable=False),
        sa.Column("createdat", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updatedat", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "rooms",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("createdat", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updatedat", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("roomid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("locationtype", locationtype_enum, nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("photo_path", sa.String(length=500), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("createdat", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updatedat", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["roomid"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("roomid", "locationtype", "label", name="uq_location_per_room"),
    )

    op.create_table(
        "items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("locationid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("expirydate", sa.Date(), nullable=True),
        sa.Column("isloanable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("isonloan", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("cabletype", sa.String(length=100), nullable=True),
        sa.Column("cablelengthmeter", sa.Numeric(12, 2), nullable=True),
        sa.Column("createdat", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updatedat", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["locationid"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("quantity >= 0", name="ck_items_quantity_non_negative"),
        sa.CheckConstraint(
            "cablelengthmeter IS NULL OR cablelengthmeter >= 0",
            name="ck_items_cablelength_non_negative",
        ),
    )

    op.create_index("ix_items_name", "items", ["name"], unique=False)

    op.create_table(
        "loans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("itemid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("borrowername", sa.String(length=200), nullable=False),
        sa.Column("loandate", sa.Date(), nullable=False),
        sa.Column("returndate", sa.Date(), nullable=True),
        sa.Column("isreturned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("createdat", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updatedat", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["itemid"], ["items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("loans")
    op.drop_index("ix_items_name", table_name="items")
    op.drop_table("items")
    op.drop_table("locations")
    op.drop_table("rooms")
    op.drop_table("users")
    locationtype_enum.drop(op.get_bind(), checkfirst=True)