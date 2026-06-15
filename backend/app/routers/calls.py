from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CallRecord
from app.schemas import (
    CallCompleteRequest,
    CallCompleteResponse,
    CallRecordItem,
    CallsListResponse,
)


VALID_OUTCOMES = {
    "booked",
    "declined",
    "ineligible",
    "transferred",
    "no_load_found",
    "unresolved",
    "unknown",
}
VALID_SENTIMENTS = {"positive", "neutral", "negative", "unknown"}

router = APIRouter(tags=["calls"])


@router.post("/api/calls/complete", response_model=CallCompleteResponse)
def complete_call(payload: CallCompleteRequest, db: Session = Depends(get_db)) -> CallCompleteResponse:
    outcome = payload.outcome if payload.outcome in VALID_OUTCOMES else "unknown"
    sentiment = payload.sentiment if payload.sentiment in VALID_SENTIMENTS else "unknown"

    record = CallRecord(
        happyrobot_run_id=payload.happyrobot_run_id,
        session_id=payload.session_id,
        mc_number=payload.mc_number,
        carrier_name=payload.carrier_name,
        load_id=payload.load_id,
        origin=payload.origin,
        destination=payload.destination,
        equipment_type=payload.equipment_type,
        loadboard_rate=payload.loadboard_rate,
        final_offer=payload.final_offer,
        outcome=outcome,
        sentiment=sentiment,
        call_summary=payload.call_summary,
        transcript=payload.transcript,
        negotiation_rounds=payload.negotiation_rounds,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return CallCompleteResponse(stored=True, call_record_id=record.id)


@router.get("/api/metrics/calls", response_model=CallsListResponse)
def list_calls(
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    outcome: str | None = Query(default=None),
    sentiment: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> CallsListResponse:
    stmt = select(CallRecord)
    count_stmt = select(func.count(CallRecord.id))

    if outcome and outcome in VALID_OUTCOMES:
        stmt = stmt.where(CallRecord.outcome == outcome)
        count_stmt = count_stmt.where(CallRecord.outcome == outcome)
    if sentiment and sentiment in VALID_SENTIMENTS:
        stmt = stmt.where(CallRecord.sentiment == sentiment)
        count_stmt = count_stmt.where(CallRecord.sentiment == sentiment)

    total = db.scalar(count_stmt) or 0
    rows = db.execute(stmt.order_by(CallRecord.created_at.desc()).offset(offset).limit(limit)).scalars().all()
    serialized = [CallRecordItem.model_validate(row) for row in rows]

    return CallsListResponse(total=total, limit=limit, offset=offset, calls=serialized)
