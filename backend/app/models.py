from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Enum, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Load(Base):
    __tablename__ = "loads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    load_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    origin: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    destination: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    pickup_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivery_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    equipment_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    loadboard_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    weight: Mapped[int | None] = mapped_column(nullable=True)
    commodity_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    num_of_pieces: Mapped[int | None] = mapped_column(nullable=True)
    miles: Mapped[int | None] = mapped_column(nullable=True)
    dimensions: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("available", "held", "booked", name="load_status"),
        default="available",
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CarrierVerification(Base):
    __tablename__ = "carrier_verifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    mc_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    dot_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dba_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    allowed_to_operate: Mapped[bool] = mapped_column(nullable=False, default=False)
    out_of_service: Mapped[bool] = mapped_column(nullable=False, default=False)
    raw_response: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class NegotiationSession(Base):
    __tablename__ = "negotiation_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    mc_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    load_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    loadboard_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_acceptable_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    round_count: Mapped[int] = mapped_column(nullable=False, default=0)
    last_carrier_offer: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    last_system_counter: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("active", "accepted", "declined", "expired", name="negotiation_status"),
        nullable=False,
        default="active",
        index=True,
    )
    final_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CallRecord(Base):
    __tablename__ = "call_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    happyrobot_run_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    mc_number: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    carrier_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    load_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    origin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    destination: Mapped[str | None] = mapped_column(String(255), nullable=True)
    equipment_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pickup_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    loadboard_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    final_offer: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    commodity_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    weight: Mapped[int | None] = mapped_column(nullable=True)
    miles: Mapped[int | None] = mapped_column(nullable=True)
    num_of_pieces: Mapped[int | None] = mapped_column(nullable=True)
    dimensions: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transfer_successful: Mapped[bool | None] = mapped_column(nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    call_duration_seconds: Mapped[int | None] = mapped_column(nullable=True)
    outcome: Mapped[str] = mapped_column(
        Enum(
            "booked",
            "declined",
            "ineligible",
            "transferred",
            "no_load_found",
            "unresolved",
            "unknown",
            name="call_outcome",
        ),
        nullable=False,
        default="unknown",
        index=True,
    )
    sentiment: Mapped[str] = mapped_column(
        Enum("positive", "neutral", "negative", "unknown", name="call_sentiment"),
        nullable=False,
        default="unknown",
        index=True,
    )
    call_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    negotiation_rounds: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
