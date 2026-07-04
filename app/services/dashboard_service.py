from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Item, Loan, Location


def get_dashboard_stats(session: Session) -> dict[str, int]:
    location_count = session.scalar(select(func.count(Location.id))) or 0
    item_count = session.scalar(select(func.count(Item.id))) or 0
    open_loan_count = session.scalar(
        select(func.count(Loan.id)).where(Loan.isreturned.is_(False))
    ) or 0
    expiry_count = session.scalar(
        select(func.count(Item.id)).where(Item.expirydate.is_not(None))
    ) or 0

    return {
        "location_count": int(location_count),
        "item_count": int(item_count),
        "open_loan_count": int(open_loan_count),
        "expiry_count": int(expiry_count),
    }
