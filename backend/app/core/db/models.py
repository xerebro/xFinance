"""Database models reflecting the normalized storage schema."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Person(Base):
    __tablename__ = "person"

    person_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, init=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    chamber: Mapped[str | None] = mapped_column(String(32))
    role: Mapped[str | None] = mapped_column(String(128))
    house_id: Mapped[str | None] = mapped_column(String(64))
    senate_id: Mapped[str | None] = mapped_column(String(64))
    oge_id: Mapped[str | None] = mapped_column(String(64))
    cik: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    filings: Mapped[list["FilingRaw"]] = relationship(back_populates="person")


class Issuer(Base):
    __tablename__ = "issuer"

    issuer_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, init=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    ticker: Mapped[str | None] = mapped_column(String(16))
    cik: Mapped[str | None] = mapped_column(String(20))
    cusip: Mapped[str | None] = mapped_column(String(16))

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="issuer")


class FilingRaw(Base):
    __tablename__ = "filing_raw"

    filing_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, init=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    source_key: Mapped[str] = mapped_column(Text, nullable=False)
    filed_date: Mapped[date | None] = mapped_column(Date)
    doc: Mapped[str | None] = mapped_column(Text)
    json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    person_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("person.person_id"))
    person: Mapped[Person | None] = relationship(back_populates="filings")

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="filing")
    positions_13f: Mapped[list["Position13F"]] = relationship(back_populates="filing")


class Transaction(Base):
    __tablename__ = "transaction"

    tx_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, init=False)
    filing_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("filing_raw.filing_id"))
    person_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("person.person_id"))
    issuer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("issuer.issuer_id"))
    action: Mapped[str | None] = mapped_column(String(16))
    quantity: Mapped[float | None] = mapped_column(Numeric)
    price: Mapped[float | None] = mapped_column(Numeric)
    amount: Mapped[float | None] = mapped_column(Numeric)
    tx_date: Mapped[date | None] = mapped_column(Date)
    ticker: Mapped[str | None] = mapped_column(String(16))
    cik: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)

    filing: Mapped["FilingRaw" | None] = relationship(back_populates="transactions")
    person: Mapped[Person | None] = relationship()
    issuer: Mapped[Issuer | None] = relationship(back_populates="transactions")


class Position13F(Base):
    __tablename__ = "position_13f"

    pos_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, init=False)
    filing_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("filing_raw.filing_id"))
    manager_name: Mapped[str | None] = mapped_column(Text)
    cik: Mapped[str | None] = mapped_column(String(20))
    cusip: Mapped[str | None] = mapped_column(String(16))
    issuer_name: Mapped[str | None] = mapped_column(Text)
    value_usd: Mapped[int | None] = mapped_column(BigInteger)
    sshPrnamt: Mapped[int | None] = mapped_column(BigInteger)
    sshPrnamtType: Mapped[str | None] = mapped_column(String(8))

    filing: Mapped["FilingRaw" | None] = relationship(back_populates="positions_13f")


__all__ = [
    "Base",
    "Person",
    "Issuer",
    "FilingRaw",
    "Transaction",
    "Position13F",
]
