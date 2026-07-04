from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Item, Loan, Location


def create_loan(
    session: Session,
    itemid,
    borrowername: str,
    loandate: date,
) -> Loan:
    item = session.get(Item, itemid)
    if item is None:
        raise ValueError("Artikel wurde nicht gefunden.")

    clean_borrower = borrowername.strip()
    if not clean_borrower:
        raise ValueError("Name ist erforderlich.")

    if not item.isloanable:
        raise ValueError("Artikel ist nicht als ausleihbar markiert.")

    if item.isonloan:
        raise ValueError("Artikel ist bereits ausgeliehen.")

    loan = Loan(
        itemid=itemid,
        borrowername=clean_borrower,
        loandate=loandate,
        isreturned=False,
    )

    item.isonloan = True
    session.add(loan)
    session.commit()
    session.refresh(loan)
    return loan


def return_loan(session: Session, loanid, returndate: date) -> Loan:
    loan = session.get(Loan, loanid)
    if loan is None:
        raise ValueError("Ausleihe wurde nicht gefunden.")

    if loan.isreturned:
        raise ValueError("Ausleihe ist bereits abgeschlossen.")

    loan.isreturned = True
    loan.returndate = returndate
    loan.item.isonloan = False

    session.commit()
    session.refresh(loan)
    return loan


def list_open_loans(session: Session) -> list[Loan]:
    stmt = (
        select(Loan)
        .options(
            joinedload(Loan.item)
            .joinedload(Item.location)
            .joinedload(Location.room)
        )
        .where(Loan.isreturned.is_(False))
        .order_by(Loan.loandate.desc())
    )
    return list(session.scalars(stmt).all())
