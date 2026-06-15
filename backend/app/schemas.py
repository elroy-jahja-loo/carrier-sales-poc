from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


OutcomeType = Literal[
    "booked",
    "declined",
    "ineligible",
    "transferred",
    "no_load_found",
    "unresolved",
    "unknown",
]
SentimentType = Literal["positive", "neutral", "negative", "unknown"]


class HealthResponse(BaseModel):
    status: str
    service: str


class CarrierVerifyRequest(BaseModel):
    mc_number: str = Field(min_length=1)


class CarrierVerifyResponse(BaseModel):
    eligible: bool
    verification_status: str
    mc_number: str
    dot_number: str | None = None
    legal_name: str | None = None
    dba_name: str | None = None
    authority_status: str | None = None
    allowed_to_operate: bool
    out_of_service: bool
    reason: str
    recommended_agent_message: str


class LoadSearchRequest(BaseModel):
    origin: str | None = None
    destination: str | None = None
    equipment_type: str | None = None
    pickup_date: date | None = None
    mc_number: str | None = None


class LoadItem(BaseModel):
    load_id: str
    origin: str
    destination: str
    pickup_datetime: datetime
    delivery_datetime: datetime
    equipment_type: str
    loadboard_rate: Decimal
    notes: str | None = None
    weight: int | None = None
    commodity_type: str | None = None
    num_of_pieces: int | None = None
    miles: int | None = None
    dimensions: str | None = None
    pitch: str


class LoadSearchResponse(BaseModel):
    found: bool
    count: int
    best_match: LoadItem | None
    loads: list[LoadItem]
    recommended_agent_message: str | None = None


class OfferEvaluateRequest(BaseModel):
    session_id: str
    mc_number: str
    load_id: str
    carrier_offer: Decimal
    round_number: int

    @field_validator("carrier_offer", mode="before")
    @classmethod
    def parse_carrier_offer(cls, value):
        return _parse_money(value)

    @field_validator("round_number", mode="before")
    @classmethod
    def parse_round_number(cls, value):
        return _parse_int(value)


class OfferEvaluateResponse(BaseModel):
    decision: Literal["accept", "counter", "decline"]
    status: str
    load_id: str
    carrier_offer: Decimal
    accepted_rate: Decimal | None = None
    counter_offer: Decimal | None = None
    round_count: int
    max_rounds: int
    message_to_carrier: str
    next_action: str


class MockTransferRequest(BaseModel):
    session_id: str
    mc_number: str
    load_id: str
    accepted_rate: Decimal

    @field_validator("accepted_rate", mode="before")
    @classmethod
    def parse_accepted_rate(cls, value):
        return _parse_money(value)


class MockTransferResponse(BaseModel):
    transfer_status: str
    mocked: bool
    message_to_carrier: str
    load_status: str


class CallCompleteRequest(BaseModel):
    happyrobot_run_id: str | None = None
    session_id: str | None = None
    mc_number: str | None = None
    carrier_name: str | None = None
    load_id: str | None = None
    origin: str | None = None
    destination: str | None = None
    equipment_type: str | None = None
    loadboard_rate: Decimal | None = None
    final_offer: Decimal | None = None
    outcome: str = "unknown"
    sentiment: str = "unknown"
    call_summary: str | None = None
    transcript: str | None = None
    negotiation_rounds: int | None = None

    @field_validator("loadboard_rate", "final_offer", mode="before")
    @classmethod
    def parse_optional_money(cls, value):
        if isinstance(value, str) and value.strip() == "":
            return None
        return _parse_money(value)

    @field_validator("negotiation_rounds", mode="before")
    @classmethod
    def parse_optional_rounds(cls, value):
        if value is None:
            return None
        if isinstance(value, str) and value.strip() == "":
            return 0
        return _parse_int(value)


class CallCompleteResponse(BaseModel):
    stored: bool
    call_record_id: int


class CallRecordItem(BaseModel):
    id: int
    created_at: datetime
    happyrobot_run_id: str | None = None
    session_id: str | None = None
    mc_number: str | None = None
    carrier_name: str | None = None
    load_id: str | None = None
    origin: str | None = None
    destination: str | None = None
    equipment_type: str | None = None
    loadboard_rate: Decimal | None = None
    final_offer: Decimal | None = None
    outcome: OutcomeType
    sentiment: SentimentType
    call_summary: str | None = None
    transcript: str | None = None
    negotiation_rounds: int | None = None

    model_config = ConfigDict(from_attributes=True)


class CallsListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    calls: list[CallRecordItem]


class MetricsSummaryResponse(BaseModel):
    total_calls: int
    verified_carriers: int
    ineligible_carriers: int
    booked_calls: int
    declined_calls: int
    no_load_found_calls: int
    unresolved_calls: int
    booking_rate: float
    average_final_offer: float
    average_loadboard_rate: float
    average_premium_percent: float
    sentiment: dict[str, int]
    outcomes: dict[str, int]
    bookings_over_time: list[dict[str, int | str]]


def _parse_money(value):
    if isinstance(value, str):
        return value.replace("$", "").replace(",", "").strip()
    return value


def _parse_int(value):
    if isinstance(value, str):
        return value.strip()
    return value
